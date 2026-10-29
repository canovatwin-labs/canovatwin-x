"""Human-readable presentation, separate from analysis and persistence."""

from .contracts import AnalysisRun


def render_text(run: AnalysisRun) -> str:
    lines = [
        f"CanovaTwin X | {run.incident_id}",
        f"Çalışma: {run.status} | Saat: {run.clock_mode} | Kaynak: sentetik",
        "Çalışan roller: " + " → ".join(r.agent_id for r in run.trace),
        f"Araç çağrısı: {run.total_tool_calls} | LLM çağrısı: {run.llm_calls}",
    ]
    if run.failure:
        lines.append(f"Engel: {run.failure.code} — {run.failure.message}")
    if run.report:
        lines.extend([f"Sonuç: {run.report.status}", run.report.summary])
        lines.extend(
            f"Bulgu: {o.message} [kanıt: {', '.join(o.evidence_ids)}]" for o in run.report.observations
        )
        for h in run.report.hypotheses:
            lines.append(f"Aday {h.fault_code}: {h.explanation}")
            lines.append(f"  Destek: {', '.join(h.supporting_evidence)}")
            if h.contradicting_evidence:
                lines.append(f"  Karşı kanıt: {', '.join(h.contradicting_evidence)}")
        research = run.report.research
        if research:
            lines.extend(
                f"Geçmiş benzerlik: {match.run_id} | skor={match.score:.3f} | doğrulanmamış adaylar"
                for match in research.historical_matches
            )
            lines.extend(
                f"Kaynak: {hit.document_id} / {hit.version} [{hit.start}:{hit.end}] — {hit.excerpt}"
                for hit in research.document_hits
            )
            lines.extend(
                f"Hipotez kontrolü {review.fault_code}: {review.verdict} — {review.reason}"
                for review in research.hypothesis_reviews
            )
            lines.extend(
                f"What-if {case.scenario_id}: son={case.final_c:.2f}°C | modelde düşüş={case.reduction_vs_baseline_c:.2f}°C"
                for case in research.simulation_cases
            )
            if research.model_adequate is not None:
                lines.append(
                    f"Model tutarlılığı: {research.model_adequate} | MAE={research.model_mae_c:.4f}°C | RMSE={research.model_rmse_c:.4f}°C"
                )
        lines.extend(f"Sınır: {limitation}" for limitation in run.report.limitations)
    return "\n".join(lines)
