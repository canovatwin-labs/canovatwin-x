"""Bounded deterministic missing-data, historical, retrieval and critique specialists."""

import re
from itertools import pairwise

from ..contracts import (
    CritiqueResult,
    DocumentHit,
    HistoricalMatch,
    HistoricalResult,
    HypothesisReview,
    MissingDataResult,
    MissingField,
    Observation,
    RetrievalResult,
)
from ..state import AnalysisContext
from .quality import BOUNDS, quality_metrics
from .shared import evidence_for


def analyze_missing_data(ctx: AnalysisContext) -> MissingDataResult:
    if ctx.request.research is None or ctx.quality is None or ctx.quality.usable:
        raise ValueError("Missing data analysis requires an invalid extended-profile window")
    samples = ctx.request.window.samples
    interval = ctx.request.research.expected_interval_s
    fields = []
    for name in BOUNDS:
        missing = [s for s in samples if getattr(s, name) is None]
        if not missing:
            continue
        longest = run = 0
        for sample in samples:
            run = run + 1 if getattr(sample, name) is None else 0
            longest = max(longest, run)
        fields.append(
            MissingField(sensor=name, missing_count=len(missing), longest_missing_s=longest * interval)
        )
    gaps = [(b.timestamp - a.timestamp).total_seconds() for a, b in pairwise(samples)]
    lost = sum(max(0, round(gap / interval) - 1) for gap in gaps if gap > ctx.policy.max_gap_s)
    age = quality_metrics(ctx)["latest_age_s"][0]
    stale = age > ctx.policy.max_age_s
    evidence = evidence_for(
        ctx,
        "A06",
        {
            "missing_fields": (float(len(fields)), "count"),
            "estimated_lost_samples": (float(lost), "count"),
            "latest_age_s": (age, "s"),
        },
    )
    observations = []
    if fields:
        observations.append(
            Observation(
                code="MISSING_SENSOR_VALUES",
                message="Eksik ölçümler sensör bazında ayrıştırıldı; değerler doldurulmadı.",
                evidence_ids=(evidence[0].evidence_id,),
            )
        )
    if lost:
        observations.append(
            Observation(
                code="STREAM_GAPS",
                message="Beklenen örnekleme aralığı varsayımıyla veri boşluğu hesaplandı.",
                evidence_ids=(evidence[1].evidence_id,),
            )
        )
    if stale:
        observations.append(
            Observation(
                code="STALE_STREAM",
                message="Son örneğin yaşı akış kesintisiyle uyumlu; fiziksel bağlantı nedeni doğrulanmadı.",
                evidence_ids=(evidence[2].evidence_id,),
            )
        )
    return MissingDataResult(
        fields=tuple(fields),
        estimated_lost_samples=lost,
        stale_stream=stale,
        observations=tuple(observations),
        evidence=evidence,
        limitation="Kayıp süre ve örnek sayısı beklenen örnekleme aralığına dayalı tahmindir; eksik veri fiziksel arıza kanıtı değildir.",
    )


def match_history(ctx: AnalysisContext) -> HistoricalResult:
    if ctx.request.research is None or ctx.anomaly is None:
        raise ValueError("Historical matching requires research inputs and anomaly findings")
    query = {o.code for o in ctx.anomaly.observations}
    start = min(s.timestamp for s in ctx.request.window.samples)
    matches, excluded = [], 0
    for case in ctx.request.research.historical_cases:
        if (
            case.asset_id != ctx.request.window.asset_id
            or case.window_end >= start
            or case.incident_id == ctx.incident_id
        ):
            excluded += 1
            continue
        codes = set(case.observation_codes)
        common = query & codes
        if common:
            matches.append(
                HistoricalMatch(
                    run_id=case.run_id,
                    score=len(common) / len(query | codes),
                    shared_observations=tuple(sorted(common)),
                    candidate_faults=case.candidate_faults,
                )
            )
    matches.sort(key=lambda m: (-m.score, m.run_id))
    selected = tuple(matches[:3])
    evidence = evidence_for(
        ctx,
        "B05",
        {f"history_score_{i}": (match.score, "ratio") for i, match in enumerate(selected)},
        source="historical_snapshot",
    )
    return HistoricalResult(matches=selected, excluded_count=excluded, evidence=evidence)


_TERMS = {
    "FAN_TRACKING": "fan feedback command speed komut geri bildirim devir",
    "LOW_AIRFLOW": "airflow fan restriction hava debi filtre",
    "LOW_COOLING": "cooling capacity soğutma kapasite",
    "LOAD_INCREASE": "load heat IT yük ısı",
    "TEMPERATURE_RISE": "temperature heat sıcaklık ısı",
    "HIGH_TEMPERATURE": "temperature heat sıcaklık ısı",
    "SENSOR_DISAGREEMENT": "sensor bias reference sensör kayma ölçüm",
    "CONTROL_OSCILLATION": "control oscillation fan kontrol salınım",
    "HUMIDITY_LOW": "humidity nem",
    "HUMIDITY_HIGH": "humidity nem",
}


def retrieve_documents(ctx: AnalysisContext) -> RetrievalResult:
    if ctx.request.research is None or ctx.anomaly is None:
        raise ValueError("Retrieval requires research inputs and investigated observations")
    query = set(
        re.findall(r"\w+", " ".join(_TERMS.get(o.code, "") for o in ctx.anomaly.observations).casefold())
    )
    hits = []
    if query:
        for doc in ctx.request.research.documents:
            for start in range(0, len(doc.content), 500):
                excerpt = doc.content[start : start + 600]
                terms = query & set(re.findall(r"\w+", excerpt.casefold()))
                if terms:
                    hits.append(
                        DocumentHit(
                            document_id=doc.document_id,
                            title=doc.title,
                            version=doc.version,
                            content_hash=doc.content_hash,
                            start=start,
                            end=start + len(excerpt),
                            excerpt=excerpt,
                            score=len(terms) / len(query),
                            matched_terms=tuple(sorted(terms)),
                        )
                    )
    hits.sort(key=lambda h: (-h.score, h.document_id, h.start))
    selected = tuple(hits[:3])
    evidence = evidence_for(
        ctx,
        "F02",
        {f"document_score_{i}": (hit.score, "ratio") for i, hit in enumerate(selected)},
        source="document_snapshot",
    )
    return RetrievalResult(hits=selected, evidence=evidence)


def critique_hypotheses(ctx: AnalysisContext) -> CritiqueResult:
    if ctx.diagnosis is None or ctx.request.research is None:
        raise ValueError("Critique requires candidate hypotheses and research inputs")
    reviews = []
    for hypothesis in ctx.diagnosis.hypotheses:
        if hypothesis.contradicting_evidence:
            verdict, reason = "weak", "Karşı kanıt var; aday desteklenmiş neden olarak sunulmamalı."
        elif hypothesis.assessment == "uncertain":
            verdict, reason = (
                "inconclusive",
                "Aynı belirti alternatif nedenlerle açıklanabilir; ek doğrulama gerekir.",
            )
        else:
            verdict, reason = (
                "retained",
                "Mevcut ölçümler adayı destekliyor; kesin fiziksel arıza doğrulaması yok.",
            )
        history = (
            tuple(m.run_id for m in ctx.history.matches if hypothesis.fault_code in m.candidate_faults)
            if ctx.history
            else ()
        )
        documents = tuple(dict.fromkeys(h.document_id for h in ctx.retrieval.hits)) if ctx.retrieval else ()
        reviews.append(
            HypothesisReview(
                fault_code=hypothesis.fault_code,
                verdict=verdict,
                reason=reason,
                supporting_evidence=hypothesis.supporting_evidence,
                contradicting_evidence=hypothesis.contradicting_evidence,
                historical_refs=history,
                document_refs=documents,
            )
        )
    return CritiqueResult(reviews=tuple(reviews))
