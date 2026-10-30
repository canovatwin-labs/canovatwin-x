"""Exercise the installed dataset CLI using a temporary local fixture."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from canovatwin.dataset_intake.models import Channel, DatasetManifest, Partition


def main() -> None:
    with TemporaryDirectory(prefix="CanovaTwin dataset test ") as directory:
        root = Path(directory)
        partitions = []
        for index, split in enumerate(("train", "validation", "test")):
            rows = ["timestamp,inlet_f,load_w"]
            rows.extend(f"2026-01-0{index + 1}T00:0{minute}:00Z,{75.2 + index},4200" for minute in range(3))
            content = ("\n".join(rows) + "\n").encode()
            path = f"{split}.csv"
            (root / path).write_bytes(content)
            partitions.append(
                Partition(
                    partition_id=split,
                    split=split,
                    asset_id=f"fixture-{index}",
                    path=path,
                    sha256=hashlib.sha256(content).hexdigest(),
                )
            )
        manifest = DatasetManifest(
            dataset_id="installed-wheel-fixture",
            source_url="https://example.org/local-fixture",
            license_identifier="MIT",
            license_note="Locally generated fixture; no third-party license claim.",
            timestamp_column="timestamp",
            expected_interval_s=60.0,
            channels={
                "inlet_c": Channel(column="inlet_f", unit="degF"),
                "it_load_kw": Channel(column="load_w", unit="W"),
            },
            partitions=tuple(partitions),
        )
        source = root / "manifest.json"
        source.write_text(manifest.model_dump_json())
        intake_file, review_file = root / "intake.json", root / "review.json"
        command = [sys.executable, "-I", "-m", "canovatwin.dataset_intake.cli", str(source)]
        subprocess.run([*command, "--output", str(intake_file)], check=True)
        subprocess.run(
            [*command, "--review-partition", "test", "--count", "3", "--output", str(review_file)],
            check=True,
        )
        intake = json.loads(intake_file.read_text())
        review = json.loads(review_file.read_text())
        assert len(intake["partitions"]) == 3
        assert intake["provenance_status"] == "declared_unverified"
        assert review["run"]["mode"] == "external_review"
        assert review["run"]["report"]["status"] == "insufficient_data"
        assert review["run"]["report"]["human_review_required"]
        assert review["label_status"] == "unknown"
        assert review["run"]["commands"] == [] and review["run"]["llm_calls"] == 0
    print("Installed dataset CLI intake and exploratory review passed")


if __name__ == "__main__":
    main()
