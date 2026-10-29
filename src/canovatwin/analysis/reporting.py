"""Reports are composed only after the evidence gate succeeds."""

from ..contracts import ResearchSummary, TechnicalReport
from ..state import AnalysisContext


def compose_report(ctx: AnalysisContext) -> TechnicalReport:
    if ctx.quality is None or ctx.verification is None or not ctx.verification.passed:
        raise ValueError("A verified analysis is required before reporting")
    if ctx.verification.checked_evidence_ids != tuple(e.evidence_id for e in ctx.evidence):
        raise ValueError("Evidence changed after verification")
    hypotheses = ctx.diagnosis.hypotheses if ctx.diagnosis else ()
    if ctx.critique:
        weak = {review.fault_code for review in ctx.critique.reviews if review.verdict == "weak"}
        hypotheses = tuple(hypothesis for hypothesis in hypotheses if hypothesis.fault_code not in weak)
    if not ctx.quality.usable:
        status = "insufficient_data"
        summary = "Veri kalitesi fiziksel arıza teşhisine yeterli değil; belirtilen ölçümler incelenmeli."
        observations = ctx.quality.issues + (ctx.missing_data.observations if ctx.missing_data else ())
    elif ctx.anomaly is not None and ctx.anomaly.detected:
        status = "needs_review"
        summary = "Anormallik bulundu; aday nedenler ve karşı kanıtlar mühendis incelemesi gerektiriyor."
        observations = ctx.anomaly.observations
    else:
        status = "clear"
        summary = "Bu zaman penceresinde uygulanan örnek kurallar bir anormallik bulmadı."
        observations = ()
    limitations = (
        "Veriler sentetiktir; fiziksel model ve eşikler tesis verisiyle kalibre edilmemiştir.",
        "Hipotezler deterministik adaylardır; doğrulanmış arıza veya olasılık tahmini değildir.",
        "Kanıt kontrolü hesapların kaynağa uygunluğunu doğrular; fiziksel nedeni kesinleştirmez.",
    )
    if status == "needs_review" and not hypotheses:
        limitations += ("Mevcut kurallar bu belirti için destekli bir kök neden adayı üretemedi.",)
    research = None
    if ctx.request.research is not None:
        research = ResearchSummary(
            missing_fields=ctx.missing_data.fields if ctx.missing_data else (),
            stale_stream=ctx.missing_data.stale_stream if ctx.missing_data else False,
            historical_matches=ctx.history.matches if ctx.history else (),
            document_hits=ctx.retrieval.hits if ctx.retrieval else (),
            hypothesis_reviews=ctx.critique.reviews if ctx.critique else (),
            simulation_cases=ctx.simulation.cases if ctx.simulation else (),
            model_adequate=ctx.simulation_validation.model_adequate if ctx.simulation_validation else None,
            model_mae_c=ctx.simulation_validation.mae_c if ctx.simulation_validation else None,
            model_rmse_c=ctx.simulation_validation.rmse_c if ctx.simulation_validation else None,
        )
        limitations += (
            "Geçmiş adaylar doğrulanmamıştır; yerel doküman eşleme sözcük tabanlıdır ve arıza kanıtı değildir.",
        )
        if ctx.simulation:
            limitations += (
                ctx.simulation.limitation,
                "Model hatası sentetik öz-tutarlılık ölçümüdür; tesis doğruluğunu göstermez.",
            )
        if ctx.simulation_validation and not ctx.simulation_validation.model_adequate:
            limitations += ("Model hata eşiğini aştı; what-if sonuçları yalnızca açıklayıcı örnektir.",)
    return TechnicalReport(
        incident_id=ctx.incident_id,
        status=status,
        summary=summary,
        observations=observations,
        hypotheses=hypotheses,
        evidence_ids=tuple(e.evidence_id for e in ctx.evidence),
        limitations=limitations,
        human_review_required=status != "clear",
        research=research,
    )
