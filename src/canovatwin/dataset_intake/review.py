"""Build an exploratory, read-only review from a fully checked CSV partition."""

import csv
import hashlib
import io
from pathlib import Path

from ..contracts import AnalysisRequest, SensorSample, TelemetryWindow
from ..policy import Policy
from ..supervisor import Supervisor
from .models import CHANNEL_UNITS, DatasetManifest, ExternalReviewReport
from .validator import MAX_BYTES, _convert, _timestamp, validate_dataset


def review_partition(
    manifest: DatasetManifest, root: Path, partition_id: str, *, offset: int = 0, count: int = 120
) -> ExternalReviewReport:
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a nonnegative integer")
    if isinstance(count, bool) or not isinstance(count, int) or not 3 <= count <= 600:
        raise ValueError("count must be an integer between 3 and 600")
    manifest = DatasetManifest.model_validate(manifest.model_dump())
    intake = validate_dataset(manifest, root)
    part = next((part for part in manifest.partitions if part.partition_id == partition_id), None)
    if part is None:
        raise ValueError("Unknown partition ID")
    path = (root / part.path).resolve()
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if hashlib.sha256(data).hexdigest() != part.sha256:
        raise ValueError("CSV changed after validation")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
    selected = []
    for index, row in enumerate(reader):
        if index < offset:
            continue
        if len(selected) == count:
            break
        values = {field: None for field in CHANNEL_UNITS}
        for name, channel in manifest.channels.items():
            raw = row[channel.column].strip()
            values[name] = _convert(float(raw), channel.unit) if raw else None
        selected.append(
            SensorSample(
                sample_id=f"{partition_id}-{index:06d}",
                timestamp=_timestamp(row[manifest.timestamp_column], partition_id, index + 2),
                **values,
            )
        )
    if len(selected) != count:
        raise ValueError("Requested review window exceeds the CSV partition")
    window = TelemetryWindow(source="declared_external", asset_id=part.asset_id, samples=tuple(selected))
    request = AnalysisRequest(window=window, as_of=selected[-1].timestamp)
    span_s = (selected[-1].timestamp - selected[0].timestamp).total_seconds()
    policy = Policy(
        max_gap_s=max(5.0, manifest.expected_interval_s * 1.5),
        max_window_s=max(3600.0, span_s + 1),
    )
    run = Supervisor(policy).run(request)
    return ExternalReviewReport(
        dataset_id=manifest.dataset_id,
        manifest_sha256=intake.manifest_sha256,
        partition_id=part.partition_id,
        asset_id=part.asset_id,
        file_sha256=part.sha256,
        source_url=manifest.source_url,
        license_identifier=manifest.license_identifier,
        offset=offset,
        count=count,
        input_sha256=hashlib.sha256(request.model_dump_json().encode()).hexdigest(),
        run=run,
    )
