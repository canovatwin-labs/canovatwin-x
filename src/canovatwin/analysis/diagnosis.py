"""Interpretable demo rules; hypotheses remain candidates, never confirmed faults."""

from ..contracts import AnomalyResult, DiagnosisResult, FaultCode, Hypothesis, Observation
from ..state import AnalysisContext


def investigate(ctx: AnalysisContext) -> AnomalyResult:
    if ctx.signals is None:
        raise ValueError("Anomaly investigation requires signal statistics")
    signals = {e.metric: e for e in ctx.signals.evidence}
    p = ctx.policy
    checks = (
        (
            "HIGH_TEMPERATURE",
            "inlet_max_c",
            lambda v: v >= p.high_inlet_c,
            "Giriş sıcaklığı örnek eşiğin üzerinde.",
        ),
        (
            "TEMPERATURE_RISE",
            "inlet_rise_c",
            lambda v: v >= p.temperature_rise_c,
            "Pencere boyunca sıcaklık yükseliyor.",
        ),
        (
            "FAN_TRACKING",
            "fan_error_pct",
            lambda v: v >= p.fan_error_pct,
            "Fan komutu ile geri bildirimi ayrışıyor.",
        ),
        (
            "LOW_AIRFLOW",
            "airflow_efficiency",
            lambda v: v < p.min_airflow_efficiency,
            "Fan geri bildirimine göre hava debisi düşük.",
        ),
        (
            "LOW_COOLING",
            "cooling_efficiency",
            lambda v: v < p.min_cooling_efficiency,
            "Hava debisine göre soğutma kapasitesi düşük.",
        ),
        (
            "LOAD_INCREASE",
            "load_increase_kw",
            lambda v: v >= p.load_increase_kw,
            "IT ısı yükü başlangıca göre yükseldi.",
        ),
        (
            "SENSOR_DISAGREEMENT",
            "sensor_disagreement_c",
            lambda v: v >= p.sensor_disagreement_c,
            "Aynı bölgenin sıcaklık sensörleri ayrışıyor.",
        ),
        ("HUMIDITY_LOW", "humidity_min_pct", lambda v: v < 30, "Nem örnek hedef aralığının altında."),
        ("HUMIDITY_HIGH", "humidity_max_pct", lambda v: v > 60, "Nem örnek hedef aralığının üzerinde."),
    )
    observations = [
        Observation(code=code, message=message, evidence_ids=(signals[key].evidence_id,))
        for code, key, predicate, message in checks
        if predicate(signals[key].value)
    ]
    if (
        signals["fan_variation_pct"].value >= p.fan_variation_pct
        and signals["fan_direction_reversals"].value >= 3
    ):
        observations.append(
            Observation(
                code="CONTROL_OSCILLATION",
                message="Fan komutunda tekrarlayan yön değişimleri var.",
                evidence_ids=(
                    signals["fan_variation_pct"].evidence_id,
                    signals["fan_direction_reversals"].evidence_id,
                ),
            )
        )
    return AnomalyResult(detected=bool(observations), observations=tuple(observations))


def diagnose(ctx: AnalysisContext) -> DiagnosisResult:
    if ctx.anomaly is None or ctx.signals is None:
        raise ValueError("Diagnosis requires an investigated anomaly")
    findings = {o.code: o for o in ctx.anomaly.observations}
    signals = {e.metric: e for e in ctx.signals.evidence}
    hypotheses = []

    def add(
        code: FaultCode,
        observation: str,
        explanation: str,
        *,
        uncertain: bool = False,
        contradictions: tuple[str, ...] = (),
    ):
        if observation in findings:
            hypotheses.append(
                Hypothesis(
                    fault_code=code,
                    explanation=explanation,
                    supporting_evidence=findings[observation].evidence_ids,
                    contradicting_evidence=contradictions,
                    assessment="uncertain" if uncertain else "candidate",
                )
            )

    add(
        FaultCode.SENSOR_BIAS,
        "SENSOR_DISAGREEMENT",
        "Sensörler ayrışıyor; hangi sensörün hatalı olduğu bağımsız ölçümle doğrulanmalı.",
        uncertain=True,
    )
    add(
        FaultCode.LOAD_SURGE,
        "LOAD_INCREASE",
        "Başlangıç penceresine göre artan IT yükü ısınmayı açıklayabilir.",
    )
    add(
        FaultCode.COOLING_LOSS,
        "LOW_COOLING",
        "Mevcut hava debisine göre düşük soğutma kapasitesi incelenmeli.",
    )
    add(
        FaultCode.FAN_MISMATCH,
        "FAN_TRACKING",
        "Komut/geri bildirim uyumsuzluğu var; sürücü ve geri bildirim ölçümü incelenmeli.",
        uncertain=True,
    )
    add(
        FaultCode.FAN_LOSS,
        "FAN_TRACKING",
        "Fan performans kaybı olası; aynı belirti geri bildirim hatasından da kaynaklanabilir.",
        uncertain=True,
    )
    add(
        FaultCode.AIRFLOW_RESTRICTION,
        "LOW_AIRFLOW",
        "Hava yolu kısıtlanması olası; fanın aerodinamik performansı da aynı belirtiyi üretebilir.",
        uncertain=True,
    )
    add(
        FaultCode.CONTROL_OSCILLATION,
        "CONTROL_OSCILLATION",
        "Tekrarlayan komut salınımı var; parametre hatası ek kontrol testi gerektirir.",
        uncertain=True,
    )
    # Keep available counter-evidence, rather than claiming every warming event is a load change.
    if "TEMPERATURE_RISE" in findings and "LOAD_INCREASE" not in findings:
        hypotheses.append(
            Hypothesis(
                fault_code=FaultCode.LOAD_SURGE,
                explanation="Isınma yük artışıyla açıklanabilir; ölçülen yük artışının küçük olması bu adayı zayıflatıyor.",
                supporting_evidence=findings["TEMPERATURE_RISE"].evidence_ids,
                contradicting_evidence=(signals["load_increase_kw"].evidence_id,),
                assessment="uncertain",
            )
        )
    return DiagnosisResult(hypotheses=tuple(hypotheses))
