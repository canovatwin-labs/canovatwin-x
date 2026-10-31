# CanovaTwin X — Güncel yetenek ve tamamlanma durumu

**31 Ekim 2026 · Uygulama 0.16.0 / Motor 0.4.0 · Sprint 16 geliştirme dalı**

Kayıtlı koşumların salt okunur karşılaştırma API'si eklendi; ana dala alınması PR incelemesine bağlıdır.
Kapsam ve sınırlar: [SPRINT_16_REPORT.md](SPRINT_16_REPORT.md).

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

15. Dış CSV veri seti için kaynak/lisans beyanını, SHA-256 dosya bütünlüğünü, sensör sütunu ve birim eşlemesini, zaman sırasını, eksik/aralık dışı ölçümleri ve varlık/zaman ayrımlı deney kümelerini çevrimdışı doğrular. Raporlanan kaynak ve lisans henüz bağımsız doğrulanmış değildir; varsayılan doğrulama komutu teşhis çalıştırmaz.

16. Doğrulanmış dış CSV parçasından seçilen 3–600 ölçümü `declared_external` kökeniyle altı uzmanlı keşif analizine verir. Kanıtlar ve çalışma kipi dış veri olarak işaretlenir; etiketler bilinmiyor, insan incelemesi her sonuçta zorunludur. Doğrudan API'de dış kaynak iddiası reddedilir. Bu yol saha teşhis başarısı olarak puanlanmaz.

17. Çevrimdışı sentetik telemetri akışında ölçüm ve geliş zamanlarını ayrı tutar; sınırlı sıra bozulmasını düzenler, geç/çift kayıtları ve tampon dolmasını açıkça reddeder. Bağlantı ve tazelik durumunu ayrı raporlar, yalnızca sıralanmış ve kesinleştirilmiş ölçümlerden analiz penceresi oluşturur. Bu bellek içi toplayıcı tek başına ağ, PLC veya kalıcı kayıt içermez.

18. Ayrı SQLite olay günlüğüyle sentetik akışa yeniden açılış sonrası devam eder. Kabul edilen işlemler atomik kaydedilir; olay sırası ve hash zinciri okunurken doğrulanır. Bozuk kayıt, eşzamanlı yazar ve başarısız disk yazısı açıkça durdurulur. Bu, canlı bağlantı veya saldırgana dayanıklı imzalı denetim günlüğü değildir.

19. CC BY 4.0 lisanslı AAU sunucu odası Zenodo v5 kaydının iki küçük yardımcı CSV dosyasını çevrimdışı ve yayıncı checksum'larıyla doğrulayarak 1.521 gerçek eşzamanlı sıcaklık çiftini içe alır. Açık saat dilimi varsayımı ve zaman ayrımlı train/validation/test raporu üretir. İki kanal dışında ölçüm ve arıza etiketi olmadığından keşif incelemesi çekimser kalır; saha teşhis puanı oluşturulmaz.

20. Figshare v3 hastane AHU dosyasını yayıncı checksum'ıyla eşleyip makalenin satır, yıl ve etiket sayılarıyla karşılaştırır. Yıl farkı, yinelenen cihaz/saat anahtarları ve boş hücreleri raporlar. Bu kaynak denetimi tanı puanı üretmez.

21. Akış laboratuvarında aynı dinamik fiziksel senaryoyu düzenli aktarım, gecikme/tekrar veya bağlantı kesintisi altında çalıştırır. Sadece kabul edilen sıralı pencere analiz edilir; reçete, ret gerekçeleri, geliş/ölçüm saatleri ve tazelik izi SQLite kaydında korunur. Panel sonucu, grafiği, filtreli olay izini ve JSON indirmeyi sunar. Bu hızlandırılmış sanal saatli tekrar, canlı cihaz bağlantısı değildir.

22. Yapılandırılmış sentetik ekipmanları ve geçmişte gözlenen kimlikleri listeler. Seçilen ekipmanın olayları, son kayıtlı penceresi, sensör etiket/birim/kalite aralıkları ve eksik değerleri ayrı görünür. Senaryo ve aktarım deneyleri ekipman hedefiyle açılır; kayıtlar ve geçmiş vakalar ekipman bazında ayrılır. Tanımlar yerel ayardan yüklenir; web üzerinden katalog düzenleme yoktur.

23. Aynı ekipmanın iki farklı kayıtlı koşumunu API üzerinden karşılaştırır: 11 kanalda mevcut ölçüm istatistikleri, eksik sayıları, aday − temel farkları, aktarım sayaçları ve değişen girdi alanları görünür. Panelden koşum seçimi sonraki adımdır; karşılaştırma yeni analiz veya geçmiş kaydı üretmez.

## Yedi katmanın durumu

### L1 — Fiziksel veya sanal cihaz: sanal pilot tamamlandı

Tek bölgeli indirgenmiş termal model, sensörler ve on arıza enjeksiyonu çalışıyor. Dinamik işletim modelinde reçete edilmiş yük/ortam değişimleri, ölçüm gürültüsü, sensör gecikmesi ve kademeli arıza davranışı var. Değerlendirme manifesti ayrıca arıza başlangıcı, şiddet, gürültü ve kayıp sensör oranını ayarlar. Gerçek cihaz, çoklu kabinet, ayrıntılı hava/nem/hidrolik modeli ve CFD yok. Bu katman fiziksel tesisle doğrulanmadı.

### L2 — Kontrol mantığı: temel simülasyon kontrolü var

Sıcaklığa bağlı deterministik oransal fan komutu, ayrı fan geri bildirimi ve arıza davranışı var. Dinamik modelde fan ve soğutma birinci dereceden gecikmeli tepki verir. Tam PLC durum makinesi, CODESYS/IEC 61131-3 programı, kontrol kodu testi ve güvenlik kontrolörü yok. Ajanlar bu kontrol çevrimine komut yazmıyor.

### L3 — Haberleşme: süreç içi/JSON sınırı var, endüstriyel bağlantı planlı

Türlü giriş sözleşmesi, zaman/kaynak kontrolü, JSON dosyası okuma ve yerel HTTP API çalışıyor. Dış CSV veri kümesi için ayrı, kaynak ve birim beyanlı doğrulama sınırı var; doğrulanmış sınırlı pencere çevrimdışı keşif analizine alınabilir. OPC UA, Modbus, gerçek gateway, kesintiden sonra ağ bağlantısı toparlama ve gerçek cihaz I/O eşlemesi uygulanmadı.

### L4 — Veri platformu: yerel kayıt ve kaynak snapshot'ları tamamlandı

SQLite, atomik kayıt, olay/çalışma ayrımı, kanıtlar, ajan izleri, revizyon, denetim geçmişi ve replay var. Yerel doküman ve geçmiş vaka snapshot'ları saklanıyor. PostgreSQL, pgvector, kurumsal kişisel hesap yönetimi, otomatik yedekleme ve üretim işletimi planlı.

### L5 — Dijital ikiz: pilot model, what-if ve tutarlılık denetimi tamamlandı

Enerji dengesi, sınırlı karşı olgusal projeksiyon, referans sıcaklık tahmini ve MAE/RMSE var. Varsayımsal parametreler kullanılıyor. Otomatik kalibrasyon, gerçek ekipman validasyonu ve geniş tesis modeli yok. Sentetik öz-tutarlılık gerçek tesis doğruluğu değildir.

### L6 — Çok ajanlı çekirdek: 12 uzmanlı çevrimdışı MVP tamamlandı

Global Supervisor, ortak fabrika, izinli araçlar, görev/araç/süre bütçeleri, iki profil ve F03/F04 doğrulama kapıları çalışıyor. Katalog 36; uygulanmış rol 12; kalan rol 24. Doğrulanmış dış veri penceresinde yalnızca mevcut core6 çalışır; kanıt kaynağı ve rapor sınırlamaları farklıdır. Grup koordinatörleri planlı. LangGraph, LLM adaptörü ve vektör RAG henüz eklenmedi. Süre sınırı işbirliklidir; güvenilmeyen harici kodu zorla sonlandıran süreç izolasyonu yok.

### L7 — Kullanıcı erişimi: CLI, API ve operasyon/deney paneli çalışıyor

Analiz, katalog, geçmiş, ayrıntı, durum değişikliği, denetim ve replay komutları var. FastAPI ile 17 HTTP yolu, okuma/yazma anahtarları ve yerel OpenAPI çalışır. Aynı servisten açılan React paneli, 11 senaryo, iki profil, olay filtresi/sayfalama, rapor, telemetri grafiği/tablosu, kanıtlar, ajan izi, durum yönetimi ve yeniden analizi sunar. Operasyon görünümünde gerçek kayıtla doldurulan tesis şeması, sayfaya ait sayaçlar ve sıcaklık/güç eğrileri vardır. Deney formu çalışma koşullarını düzenler; telemetri ekranı ayrıca fan grafiğini sunar. Çevrimdışı deney CLI'si üç yöntemi karşılaştırıp raporlar; veri seti CLI'si dış CSV dosyalarını doğrular ve isteğe bağlı sınırlı keşif incelemesi yapar. Henüz panelde bir karşılaştırma veya dış veri ekranı yok. Eski ölçümler canlı olarak sunulmaz. Ayrı kapsamlı Agent Workbench, çoklu deney karşılaştırmalı Digital Twin Lab ve kişisel kullanıcı yönetimi henüz yoktur.

Akış laboratuvarı, L3'ün çevrimdışı aktarım deneyini L4'te kayıtlı reçete ve
L7'de operatör akışına bağlar. Toplam 17 HTTP yolu vardır. Varlık kataloğu ve ekipman bazlı geçmiş/deney akışı vardır. Gerçek gateway
ve arka planda sürekli oturum hâlâ uygulanmadı.

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

- Sprint 9: doğrulanmış dış CSV'den sınırlı keşif incelemesi, ayrı çalışma ve kanıt kökeni, bilinmeyen etiket ve zorunlu insan incelemesi. Gerçek veri seti ve saha puanı hâlâ yok.

- Sprint 10: sentetik telemetri için ölçüm/geliş zamanını ayıran sınırlı akış toplayıcısı, sıra bozulması, geç/çift veri, tampon dolması ve bağlantı/tazelik durumları. Canlı ağ ve PLC bağlantısı yok.

- Sprint 11: ayrı SQLite olay günlüğü, atomik yazma, hash zinciriyle bozulma kontrolü, yeniden açılışta deterministik akış kurtarma ve eşzamanlı yazar reddi. Canlı gateway yok.

- Sprint 12: lisansı ve sürümü kayıtlı bağımsız AAU sunucu odası sıcaklıklarını kaynak hash'leriyle içe alma, aynı anda ölçülmüş iki kanal ve zaman ayrımlı deney kümeleri; sınırlı keşif analizi ve açık yetersiz veri sonucu. Arıza etiketi ve saha teşhis puanı yok.

- Sprint 13: yayıncı sürümüne sabit hastane AHU kaynak denetimi; tarihin makaleyle uyuşmaması, çift kayıtlar ve boş ölçümler görünür. Bağımsız teşhis doğrulaması açık.

- Sprint 14: üç aktarım profili, katı olay izi ve pencere eşleşmesi, kalıcı deney metadatası, yeni API yolu, akış çalışma alanı ve JSON dışa aktarma. Ajan sayısı değişmedi.

- Sprint 15: sürümlü sentetik varlık/etiket kataloğu, ekipman bazlı geçmiş sayfalama, iki bağımsız sentetik hedef, eski kayıt uyumluluğu ve operatör inceleme alanı.

- Sprint 16: salt okunur, aynı ekipmanla sınırlı kayıtlı koşum karşılaştırma API'si. Yeni ajan veya panel ekranı eklenmedi.

## Doğrulama ve sınırlar

Sprint 16: 629 Python / 50 panel testi geçti; toplam kapsam %94,95. Karşılaştırma modülü, okuma yetkisi, değişmeyen audit ve kurulu 0.16.0 paketin gerçek HTTP yolu doğrulandı. Yeni panel ekranı yoktur. Ayrıntı: [SPRINT_16_REPORT.md](SPRINT_16_REPORT.md).


Sprint 15'te 618 Python testi ve 50 arayüz testi geçti; kod/biçim, TypeScript ve Vite 8 üretim derlemesi temiz. Python toplam satır+dal kapsamı %94,86; bu oran bilimsel teşhis başarısı değildir. 11 fiziksel senaryo × 3 aktarım profili, sınır örnek sayıları, bozuk iz, yetki, kayıt sonrası uygulamayı yeniden açma ve yeniden analiz sınandı. Tam npm audit sıfır bulgu verdi. Önceki 11 senaryo × 3 iş yükü profili testleri korunuyor.

Sprint 15'te temiz ortamda kurulu 0.15.0 paketi ve gerçek HTTP üzerinden 22 referans + 33 dinamik birleşim ve üç aktarım profili, kimlik/yetki, kalıcı kayıt, durum, replay, sürüm/şema, panel varlıkları ve dört eşzamanlı yazma doğrulandı. Aynı kurulu pakette 66 yöntem/vaka değerlendirmesi tamamlandı; Sprint 7'nin süreler dışındaki sonuç hash'i değişmedi. Dış veri CLI'si üç parçalı yerel test dosyasında içe alma ve keşif incelemesi yaptı. Önceki sprintin kayıtları yeni deney metadatası olmadan okunup yeniden analiz edilebilir. WebKit'te Sprint 6 kapsamında dinamik ayarlarla deney, iletişim eskimesi uyarısı, üç grafik, replay, oturum temizliği ve dar/yatay/geniş ekran akışları kontrol edildi. Sprint 9 yeni panel akışı eklemedi.

Henüz yapılmayanlar: çok kanallı ve arıza etiketli bağımsız HVAC veri kümesiyle teşhis doğrulaması, LLM/klasik ML baseline karşılaştırması, bağımsız veri üzerinde Macro-F1/Top-3 doğruluk, bilimsel güven aralıkları, gerçek şirket verisi ve donanım validasyonu. AAU veri kümesinin saat dilimi varsayımı yayıncı tarafından doğrulanmış değildir. Tüm ajanlar bu sürümde deterministik araç kullanır; eğitilmiş model veya 36 LLM çağrısı yoktur.

Üretim emniyet sistemi, tam kurumsal ürün veya gerçek tesis dijital ikizi doğruluğu iddiası yoktur. Şubat 2027 sonrası şirketin izin verdiği donanıma salt okunur adaptör eklemek ileri kapsamdır.

## GitHub kalite kapısı — 30 Ekim

Public/MIT organizasyon deposu, ayrı hesaplarla katkı ve inceleme düzeni kuruldu.
Python 3.12 sözleşme farkı giderildi; üç Python sürümünde Linux CI doğrulandı.
Ana dalda üç kalite kontrolü zorunlu; mevcut yönetici istisnası korunuyor.
Ayrıntılar ve sınırlar [GitHub devir raporunda](GITHUB_HANDOFF_REPORT.md).
Bu altyapı adımı yeni uzman veya saha yeteneği eklemedi.
