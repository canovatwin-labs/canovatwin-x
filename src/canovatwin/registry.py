"""Canonical A01–F06 catalog from the supplied project proposal."""

from types import MappingProxyType
from typing import Literal

from .contracts import AgentId, Contract


class AgentDefinition(Contract):
    agent_id: AgentId
    name: str
    group: Literal["A", "B", "C", "D", "E", "F"]
    purpose: str
    version: Literal["1.0"] = "1.0"
    status: Literal["active", "planned"]
    activation_stage: Literal[6, 12] | None
    execution: Literal["deterministic", "unimplemented"]
    read_only: Literal[True] = True
    allowed_tools: tuple[str, ...]
    input_schema: str = "AnalysisContext/v1"
    output_schema: str


_CATALOG = (
    ("A01", "Data Supervisor", "Veri inceleme görevlerini yönetme"),
    ("A02", "Sensor Validator", "Aralık, güncellik ve tutarlılık kontrolü"),
    ("A03", "Signal Analyzer", "Zaman penceresinde trend ve sinyal analizi"),
    ("A04", "Drift Detector", "Sensör kayması ve davranış sapması"),
    ("A05", "Data Fusion", "Çoklu ölçümleri birleştirme"),
    ("A06", "Missing Data Analyst", "Kayıp veri ve bağlantı sorunu analizi"),
    ("B01", "Fault Supervisor", "Arıza araştırmasını yönetme"),
    ("B02", "Anomaly Investigator", "Anormal olayın bağlamsal analizi"),
    ("B03", "Root Cause Analyst", "Kanıtlı kök neden adayları"),
    ("B04", "Fault Correlator", "Eş zamanlı belirtilerin ilişkisi"),
    ("B05", "Historical Case Matcher", "Benzer arızaları bulma"),
    ("B06", "Hypothesis Critic", "Karşı hipotez ve çelişki analizi"),
    ("C01", "Maintenance Supervisor", "Bakım görev koordinasyonu"),
    ("C02", "Maintenance Planner", "Bakım seçenekleri önerisi"),
    ("C03", "Component Health Analyst", "Ekipman sağlık değerlendirmesi"),
    ("C04", "Failure Risk Analyst", "Risk göstergeleri"),
    ("C05", "Spare Parts Analyst", "Parça gereksinimi inceleme"),
    ("C06", "Maintenance History Analyst", "Bakım kayıtlarını ilişkilendirme"),
    ("D01", "Twin Supervisor", "Simülasyon orkestrasyonu"),
    ("D02", "Simulation Designer", "What-if senaryoları oluşturma"),
    ("D03", "Thermal Analyst", "Sıcaklık ve ısı yükü analizi"),
    ("D04", "Energy Analyst", "Enerji kullanım değerlendirmesi"),
    ("D05", "Parameter Calibration Agent", "Model parametrelerini ayarlama"),
    ("D06", "Simulation Validator", "Modelin tahmin hatasını ölçme"),
    ("E01", "PLC Supervisor", "PLC test görevlerini dağıtma"),
    ("E02", "PLC Code Analyzer", "Kontrol kodunun statik analizi"),
    ("E03", "Change Impact Analyst", "Değişiklik etki analizi"),
    ("E04", "Test Generator", "Test senaryosu üretimi"),
    ("E05", "Test Execution Agent", "İzole test ortamında senaryo çalıştırma"),
    ("E06", "Regression Analyst", "Eski/yeni test sonuçlarını karşılaştırma"),
    ("F01", "Knowledge Supervisor", "Bilgi iş akışını yönetme"),
    ("F02", "Technical Document Retriever", "Doküman ve RAG araması"),
    ("F03", "Evidence Verifier", "Kanıt ve iddia geçerlilik kontrolü"),
    ("F04", "Report Composer", "Teknik arıza raporu"),
    ("F05", "Operator Assistant", "Doğal dil soru-cevap"),
    ("F06", "Recommendation Reviewer", "Öneri ve risk tutarlılık kontrolü"),
)
CORE = {
    "A02": ("check_sensor_quality", "quality"),
    "A03": ("calculate_statistics", "signals"),
    "B02": ("detect_anomalies", "anomaly"),
    "B03": ("evaluate_causes", "diagnosis"),
    "F03": ("verify_evidence", "verification"),
    "F04": ("generate_report", "report"),
}
EXTENDED = {
    "A06": ("analyze_missing_data", "missing_data"),
    "B05": ("match_history", "history"),
    "B06": ("critique_hypotheses", "critique"),
    "D02": ("design_simulation", "simulation"),
    "D06": ("validate_simulation", "simulation_validation"),
    "F02": ("retrieve_documents", "retrieval"),
}
IMPLEMENTED = {**CORE, **EXTENDED}
_STAGE_12 = frozenset({"A06", "B05", "B06", "D02", "D06", "F02"})
REGISTRY = tuple(
    AgentDefinition(
        agent_id=id_,
        name=name,
        group=id_[0],
        purpose=purpose,
        status="active" if id_ in IMPLEMENTED else "planned",
        activation_stage=6 if id_ in CORE else 12 if id_ in _STAGE_12 else None,
        execution="deterministic" if id_ in IMPLEMENTED else "unimplemented",
        allowed_tools=(IMPLEMENTED[id_][0],) if id_ in IMPLEMENTED else (),
        output_schema=IMPLEMENTED[id_][1] if id_ in IMPLEMENTED else "unimplemented",
    )
    for id_, name, purpose in _CATALOG
)
BY_ID = MappingProxyType({agent.agent_id: agent for agent in REGISTRY})
ACTIVE_IDS = tuple(agent.agent_id for agent in REGISTRY if agent.status == "active")
