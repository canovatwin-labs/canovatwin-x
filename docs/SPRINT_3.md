# Sprint 3 — On iki uzmanlı çevrimdışı çekirdek

## Kabul ölçütleri

1. Önceki 181 test ve kaynak yedeğiyle temeli doğrula.
2. A06 eksik veri, B05 geçmiş olay eşleme, B06 hipotez eleştirisi, D02 what-if tasarımı, D06 model doğrulama ve F02 kaynaklı doküman erişimini uygula.
3. Altı rollük karşılaştırma profilini koru; on iki rollük profili dinamik çalıştır. Her olayda tüm rolleri çağırma.
4. Geçmiş/doküman/model ayarlarını girişte dondur; tekrar çalıştırma canlı kaynaklardan etkilenmesin. Önceki sürüm kayıtlarının okunmasını koru.
5. Yeni çıktıları kanıt doğrulama ve rapora dahil et. Yanlış kaynak, değiştirilmiş sonuç, eksik veri ve yetersiz model testlerini geçir.
6. Senaryo ve profil karşılaştırmalarını değerlendir; temiz kurulum ve tüm kalite kontrollerinden sonra sprint raporunu kapat.
7. Güncel yetenekleri, yedi katmanı ve 36 rolün durumunu ayrı bir proje durum belgesinde açıkla.

Doküman erişimi bu sprintte yerel ve sözcük tabanlıdır; vektör araması/LLM ile RAG tamamlandı sayılmaz. Simülasyon doğrulaması sentetik model tutarlılığıdır; tesis kalibrasyonu değildir. Geçmiş hipotezler doğrulanmış arıza gibi kullanılmaz. Gerçek PLC ve şirket verisi kapsamda değildir.

## Kapanış

- [x] 181 testlik başlangıç ve kaynak yedeği doğrulandı.
- [x] Altı yeni rol uygulandı; toplam 12 rol uygun senaryolarda çalıştırıldı.
- [x] core6/mvp12 profilleri ve kaynaklara göre yönlendirme doğrulandı.
- [x] Snapshot replay ve 0.3.0 kayıt okuma uyumluluğu test edildi.
- [x] Sahte kaynak/çıktı, model yetersizliği ve sınırlar test edildi.
- [x] 242 test ve kod/biçim kontrolleri geçti; 66 analiz değerlendirildi.
- [x] Temiz paket kurulumuyla 22 profil/senaryo ve geçmişli akış geçti.
- [x] Sprint raporu ve katman/ajan durum belgesi tamamlandı.
