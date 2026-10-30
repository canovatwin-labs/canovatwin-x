# CanovaTwin X — Güncel yetenek ve tamamlanma durumu

**30 Ekim 2026 · Uygulama 0.9.0 / Motor 0.4.0 · Sprint 8 geliştirme dalında**

Çalışan çıktı: sentetik veriyle yerel web paneli, API ve CLI ile kullanılabilen, kanıta dayalı rapor ve kalıcı inceleme geçmişi üreten 12 uzmanlı karar destek çekirdeği. Katalog 36 rol içerir. Bu belge tamamlanmış özelliği, kısmi katmanı ve planlı rolü birbirinden ayırır; tamamlanma yüzdesi iddiası taşımaz.

## Proje bugün neler yapabiliyor?

1. Tek termal bölge ve soğutma ünitesi için sıcaklık, nem, fan komutu/geri bildirimi, hava debisi, IT yükü ve soğutma kapasitesi üretir. Normal çalışma ve on arıza senaryosu vardır. Dinamik modelde sabit/dalgalı/toplu işlem iş yükleri, ayarlanabilir ortam ve yük, fan/soğutma/sensör gecikmeleri ve kademeli arızalar çalışır; önceki referans model korunur.
2. Eksik, eski, gelecek tarihli, aralık dışı veya tutarsız telemetriyi tespit eder. Eksik veriyi doldurmadan sensör ve akış sorunu olarak raporlar.
3. Zaman penceresinde sıcaklık eğimi, varyans, uygun durumda korelasyon ve ekipman oranlarını hesaplar; örnek kurallarla anormallikleri araştırır.
4. Destek ve karşı kanıtlarla neden adayları oluşturur. Eleştirmen zayıf adayları nihai listeden ayırır; belirsiz olanlar kesin teşhis olarak sunulmaz.
5. Aynı ekipmanın önceki, örtüşmeyen analizlerini belirtiler üzerinden eşler. Geçmiş adaylar doğrulanmamış olarak kalır.
6. Yerel dokümanlarda sözcük tabanlı arama yapar; alıntıyı doküman sürümü, hash ve karakter konumuyla gösterir. Üç demo notu hazırdır; kullanıcı kendi JSON notlarını verebilir.
7. Desteklenen adaylar için nominal kapasite sınırında what-if sıcaklık hesabı yapar; model hatasını MAE/RMSE ile ölçer. Yetersiz modelde sonuçları sınırlı örnek olarak işaretler.
8. Hesapları, kaynak bağlantılarını ve raporu kontrol eder. Bozuk uzman çıktısı veya doğrulama hatasında nihai raporu engeller.
9. Girdi, politika, sonuç, kanıt, ajan izi ve araştırma kaynaklarını SQLite'a kaydeder. Dinamik deneyin üretici sürümü, ayarları, tohumu ve başlangıcı uzman girdilerinden ayrı saklanır. Olay inceleme durumunu gerekçeli ve revizyon kontrollü yönetir.
10. Saklanan girdilerle yeniden analiz yapar; süreler dışındaki sonuç farklarını gösterir. Sonradan eklenen geçmiş/dokümanlar eski çalışmayı değiştirmez.
11. CLI üzerinden Türkçe metin veya JSON çıktı verir. `core6` ve `mvp12` profilleri seçilebilir. Sıfır LLM çağrısı ve sıfır fiziksel komutla çalışır.

12. Yerel HTTP üzerinden analiz, katalog, geçmiş, durum ve replay işlemlerini sunar. Okuma/yazma yetkileri, katı JSON doğrulaması, boyut sınırı, hata zarfı ve OpenAPI vardır.

13. Türkçe React panelinden senaryo üretir; olay, rapor, telemetri, kanıt, ajan izi ve geçmişi gösterir. Gerekçeli durum değişimi ve yeniden analiz API üzerinden kaydedilir. Okuma/yazma yetkisi sunucudan öğrenilir; anahtar yalnızca sekme belleğinde tutulur.

14. Sürümlü sentetik deney manifestiyle train/validation/test kümelerini ayırır; arıza başlangıcı, şiddeti, gürültü ve eksik sensör oranını değiştirir. Aynı 22 test vakasında eşik yöntemi, core6 ve mvp12 sonuçlarını JSON/CSV/Markdown olarak dışa aktarır. Alarm, aday, kapsama ve süre metrikleri hesaplar; deney çevrimdışıdır ve bağımsız saha doğrulaması değildir.

15. Dış CSV veri seti için kaynak/lisans beyanını, SHA-256 dosya bütünlüğünü, sensör sütunu ve birim eşlemesini, zaman sırasını, eksik/aralık dışı ölçümleri ve varlık/zaman ayrımlı deney kümelerini çevrimdışı doğrular. Raporlanan kaynak ve lisans henüz bağımsız doğrulanmış değildir; içe alınan veri teşhis motoruna aktarılmaz.

## Yedi katmanın durumu

### L1 — Fiziksel veya sanal cihaz: sanal pilot tamamlandı

Tek bölgeli indirgenmiş termal model, sensörler ve on arıza enjeksiyonu çalışıyor. Dinamik işletim modelinde reçete edilmiş yük/ortam değişimleri, ölçüm gürültüsü, sensör gecikmesi ve kademeli arıza davranışı var. Değerlendirme manifesti ayrıca arıza başlangıcı, şiddet, gürültü ve kayıp sensör oranını ayarlar. Gerçek cihaz, çoklu kabinet, ayrıntılı hava/nem/hidrolik modeli ve CFD yok. Bu katman fiziksel tesisle doğrulanmadı.

### L2 — Kontrol mantığı: temel simülasyon kontrolü var

Sıcaklığa bağlı deterministik oransal fan komutu, ayrı fan geri bildirimi ve arıza davranışı var. Dinamik modelde fan ve soğutma birinci dereceden gecikmeli tepki verir. Tam PLC durum makinesi, CODESYS/IEC 61131-3 programı, kontrol kodu testi ve güvenlik kontrolörü yok. Ajanlar bu kontrol çevrimine komut yazmıyor.

### L3 — Haberleşme: süreç içi/JSON sınırı var, endüstriyel bağlantı planlı

Türlü giriş sözleşmesi, zaman/kaynak kontrolü, JSON dosyası okuma ve yerel HTTP API çalışıyor. Dış CSV veri kümesi için ayrı, kaynak ve birim beyanlı doğrulama sınırı var; motorla bağlantısı yok. OPC UA, Modbus, gerçek gateway, kesintiden sonra ağ bağlantısı toparlama ve gerçek cihaz I/O eşlemesi uygulanmadı.

### L4 — Veri platformu: yerel kayıt ve kaynak snapshot'ları tamamlandı

SQLite, atomik kayıt, olay/çalışma ayrımı, kanıtlar, ajan izleri, revizyon, denetim geçmişi ve replay var. Yerel doküman ve geçmiş vaka snapshot'ları saklanıyor. PostgreSQL, pgvector, kurumsal kişisel hesap yönetimi, otomatik yedekleme ve üretim işletimi planlı.

### L5 — Dijital ikiz: pilot model, what-if ve tutarlılık denetimi tamamlandı

Enerji dengesi, sınırlı karşı olgusal projeksiyon, referans sıcaklık tahmini ve MAE/RMSE var. Varsayımsal parametreler kullanılıyor. Otomatik kalibrasyon, gerçek ekipman validasyonu ve geniş tesis modeli yok. Sentetik öz-tutarlılık gerçek tesis doğruluğu değildir.

### L6 — Çok ajanlı çekirdek: 12 uzmanlı çevrimdışı MVP tamamlandı

Global Supervisor, ortak fabrika, izinli araçlar, görev/araç/süre bütçeleri, iki profil ve F03/F04 doğrulama kapıları çalışıyor. Katalog 36; uygulanmış rol 12; kalan rol 24. Grup koordinatörleri planlı. LangGraph, LLM adaptörü ve vektör RAG henüz eklenmedi. Süre sınırı işbirliklidir; güvenilmeyen harici kodu zorla sonlandıran süreç izolasyonu yok.

### L7 — Kullanıcı erişimi: CLI, API ve operasyon/deney paneli çalışıyor

Analiz, katalog, geçmiş, ayrıntı, durum değişikliği, denetim ve replay komutları var. FastAPI ile 13 HTTP yolu, okuma/yazma anahtarları ve yerel OpenAPI çalışır. Aynı servisten açılan React paneli, 11 senaryo, iki profil, olay filtresi/sayfalama, rapor, telemetri grafiği/tablosu, kanıtlar, ajan izi, durum yönetimi ve yeniden analizi sunar. Operasyon görünümünde gerçek kayıtla doldurulan tesis şeması, sayfaya ait sayaçlar ve sıcaklık/güç eğrileri vardır. Deney formu çalışma koşullarını düzenler; telemetri ekranı ayrıca fan grafiğini sunar. Çevrimdışı deney CLI'si üç yöntemi karşılaştırıp raporlar; ayrı veri seti CLI'si dış CSV dosyalarını analize bağlamadan doğrular. Henüz panelde bir karşılaştırma veya dış veri ekranı yok. Eski ölçümler canlı olarak sunulmaz. Ayrı kapsamlı Agent Workbench, çoklu deney karşılaştırmalı Digital Twin Lab ve kişisel kullanıcı yönetimi henüz yoktur.

## 36 ajan rolünün tek tek durumu

Global Supervisor aşağıdaki 36 rolün dışındadır ve çalışır durumdadır. Planlı rolün adına benzer bir araç bulunması, o rolün uygulanmış olduğu anlamına gelmez.

### A — Sensör ve veri zekâsı

- **A01 Data Supervisor — Planlı.** Grup koordinatörü henüz yok.
- **A02 Sensor Validator — Çalışıyor.** Aralık, zaman, kimlik ve fiziksel tutarlılık kontrolü.
- **A03 Signal Analyzer — Çalışıyor.** Pencere istatistikleri, trend, varyans ve korelasyon.
- **A04 Drift Detector — Planlı.** Bağımsız kayma uzmanı yok; mevcut sensör farkı kuralı bunun tamamlandığı anlamına gelmez.
- **A05 Data Fusion — Planlı.** Çoklu ölçüm birleştirme uzmanı yok.
- **A06 Missing Data Analyst — Çalışıyor.** Sensör bazlı eksik değer ve akış boşluğu analizi.

### B — Arıza ve kök neden

- **B01 Fault Supervisor — Planlı.** Grup koordinatörü henüz yok.
- **B02 Anomaly Investigator — Çalışıyor.** Belirtilerin bağlamsal kural analizi.
- **B03 Root Cause Analyst — Çalışıyor.** Deterministik adaylar ve destek/karşı kanıtlar.
- **B04 Fault Correlator — Planlı.** Ayrı olay korelasyon uzmanı yok.
- **B05 Historical Case Matcher — Çalışıyor.** Sınırlı, zamansal olarak uygun geçmiş belirti eşleme.
- **B06 Hypothesis Critic — Çalışıyor.** Adayları eleştirme, zayıfları ayırma ve belirsizliği koruma.

### C — Bakım ve güvenilirlik

- **C01 Maintenance Supervisor — Planlı.**
- **C02 Maintenance Planner — Planlı.**
- **C03 Component Health Analyst — Planlı.**
- **C04 Failure Risk Analyst — Planlı.**
- **C05 Spare Parts Analyst — Planlı.**
- **C06 Maintenance History Analyst — Planlı.**

Bakım önerisi, ekipman sağlık puanı, risk tahmini ve parça planlaması bu sürümün tamamlanmış özellikleri değildir.

### D — Dijital ikiz ve simülasyon

- **D01 Twin Supervisor — Planlı.** Grup koordinatörü henüz yok.
- **D02 Simulation Designer — Çalışıyor.** Desteklenen adaylardan sınırlı what-if senaryoları oluşturup hesaplama.
- **D03 Thermal Analyst — Planlı.** Termal hesap aracı var; ayrı uzman rol henüz yok.
- **D04 Energy Analyst — Planlı.** Enerji verimliliği/PUE uzmanı yok.
- **D05 Parameter Calibration Agent — Planlı.** Otomatik kalibrasyon yok.
- **D06 Simulation Validator — Çalışıyor.** Referans ölçüme göre MAE/RMSE ve model yeterliliği kontrolü.

### E — PLC ve yazılım doğrulama

- **E01 PLC Supervisor — Planlı.**
- **E02 PLC Code Analyzer — Planlı.**
- **E03 Change Impact Analyst — Planlı.**
- **E04 Test Generator — Planlı.**
- **E05 Test Execution Agent — Planlı.**
- **E06 Regression Analyst — Planlı.**

Python testlerinin bulunması bu PLC uzmanlarının tamamlandığı anlamına gelmez. Gerçek kontrolör bağlantısı, kontrol kodu analizi ve PLC regresyon testi henüz yok.

### F — Bilgi ve raporlama

- **F01 Knowledge Supervisor — Planlı.** Grup koordinatörü henüz yok.
- **F02 Technical Document Retriever — Çalışıyor.** Yerel sözcük tabanlı, sürümlü kaynak erişimi; semantik RAG değil.
- **F03 Evidence Verifier — Çalışıyor.** Telemetri ve dondurulmuş kaynaklardan sonuçların yeniden hesaplanması/doğrulanması.
- **F04 Report Composer — Çalışıyor.** Doğrulanmış sonuç, kaynak, eleştiri ve model değerlendirmesiyle rapor.
- **F05 Operator Assistant — Planlı.** Doğal dil sohbet arayüzü yok.
- **F06 Recommendation Reviewer — Planlı.** Ayrı öneri/risk uzmanı yok.

## Tamamlanan sprint çıktıları

- Sprint 1: ilk altı uzman, katı sözleşmeler, sentetik veri ve güvenli çekirdek.
- Sprint 2: kalıcı kayıt, yaşam döngüsü, denetim ve tekrar çalıştırma.
- Sprint 3: diğer altı uzman, kaynak snapshot'ları, eleştiri, what-if ve model denetimi; altı/on iki rol profilleri.
- Sprint 4: yerel, kimliği doğrulanan API; yetki, sözleşme ve hata sınırları; gerçek HTTP doğrulaması.

- Sprint 5: aynı servisten açılan React paneli, bellek içi oturum, gerçek API ile operatör akışları; tarayıcı, arayüz ve paket doğrulaması. Yeni uzman eklenmedi.

- Sprint 6: üç dinamik iş yükü profili, gecikmeli ekipman/sensör tepkisi, kademeli arızalar ve kayıtlı deney koşulları; daha yoğun operasyon ekranı, tesis şeması ve üç telemetri grafiği. Ajan sayısı değişmedi.

- Sprint 7: seed ayrımlı sentetik manifest, değişken enjeksiyon, bağımsız eşik tabanı ile core6/mvp12 karşılaştırması, hata/kapsama/süre metrikleri ve tekrar üretilebilir çevrimdışı raporlar. Ajan sayısı değişmedi.

- Sprint 8: dış veri için çevrimdışı CSV doğrulama sözleşmesi, birim dönüşümü, veri kalitesi özeti, hash ve split sızıntı kontrolleri. Gerçek veri seti henüz seçilmedi ve teşhis motoruna bağlanmadı.

## Doğrulama ve sınırlar

519 Python testi ve 39 arayüz testi geçti; kod/biçim, TypeScript ve üretim derlemesi temiz. Python toplam satır+dal kapsamı %97,25; bu oran arayüz kapsam oranı veya bilimsel teşhis başarısı değildir. Yeni 12 test, dış veri doğrulamasının normal ve hata sınırlarını kapsar. 11 senaryo × 3 iş yükü profili için kayıt, replay ve beklenen rapor/aday davranışları önceki testlerle korunuyor.

Temiz ortamda kurulu dağıtım paketi ve gerçek HTTP üzerinden 22 referans + 33 dinamik birleşim, kimlik/yetki, kalıcı kayıt, durum, replay, sürüm/şema, panel varlıkları ve dört eşzamanlı yazma doğrulandı. Aynı kurulu pakette 66 yöntem/vaka değerlendirmesi tamamlandı; Sprint 7'nin süreler dışındaki sonuç hash'i değişmedi. Yeni dış veri CLI'si üç parçalı yerel test dosyasında kurulu wheel'den çalıştırıldı. Önceki sprintin kayıtları yeni deney metadatası olmadan okunup yeniden analiz edilebilir. WebKit'te Sprint 6 kapsamında dinamik ayarlarla deney, iletişim eskimesi uyarısı, üç grafik, replay, oturum temizliği ve dar/yatay/geniş ekran akışları kontrol edildi. Sprint 8 yeni panel akışı eklemedi.

Henüz yapılmayanlar: açık HVAC veri setini seçip lisansını doğrulayarak gerçekten içe alma, dış veriyi analize bağlama, LLM/klasik ML baseline karşılaştırması, bağımsız veri üzerinde Macro-F1/Top-3 doğruluk, bilimsel güven aralıkları, gerçek şirket verisi ve donanım validasyonu. Tüm ajanlar bu sürümde deterministik araç kullanır; eğitilmiş model veya 36 LLM çağrısı yoktur.

Üretim emniyet sistemi, tam kurumsal ürün veya gerçek tesis dijital ikizi doğruluğu iddiası yoktur. Şubat 2027 sonrası şirketin izin verdiği donanıma salt okunur adaptör eklemek ileri kapsamdır.

## GitHub kalite kapısı — 30 Ekim

Public/MIT organizasyon deposu, ayrı hesaplarla katkı ve inceleme düzeni kuruldu.
Python 3.12 sözleşme farkı giderildi; üç Python sürümünde Linux CI doğrulandı.
Ana dalda üç kalite kontrolü zorunlu; mevcut yönetici istisnası korunuyor.
Ayrıntılar ve sınırlar [GitHub devir raporunda](GITHUB_HANDOFF_REPORT.md).
Bu altyapı adımı yeni uzman veya saha yeteneği eklemedi.
