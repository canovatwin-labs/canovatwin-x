"""Small, explicitly illustrative corpus. Document text is data, never instructions."""

from .contracts import TechnicalDocument


def demo_documents() -> tuple[TechnicalDocument, ...]:
    texts = (
        (
            "DEMO-FAN",
            "Fan ve hava debisi inceleme notu",
            "Fan command and feedback should be compared separately from airflow. Düşük hava debi, fan performansı veya filtre kısıtlanmasıyla ilişkili olabilir. Komut ve geri bildirim farkı sürücü ya da ölçüm hatasından kaynaklanabilir. Bu demo notu arızayı doğrulamaz.",
        ),
        (
            "DEMO-THERMAL",
            "Isı yükü ve soğutma notu",
            "Temperature depends on IT heat load, cooling capacity and ambient heat transfer. Isı yük artışı ile soğutma kapasite kaybı ayrı değerlendirilmelidir. Simülasyon sıcaklık düşüşü fiziksel arıza nedenini kanıtlamaz.",
        ),
        (
            "DEMO-SENSOR",
            "Sensör kalitesi inceleme notu",
            "Sensor bias and missing measurements require reference comparisons. Sensör kayma ve ölçüm farkları bağımsız referansla incelenir. Eksik veri doldurularak kesin teşhis üretilmemelidir. Control oscillation kontrol salınımı ayrı test gerektirir.",
        ),
    )
    return tuple(
        TechnicalDocument(
            document_id=id_, title=title, version="demo-1", content=content, source_kind="demo_reference"
        )
        for id_, title, content in texts
    )
