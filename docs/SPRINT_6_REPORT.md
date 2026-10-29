# CanovaTwin X — Sprint 6 sonuç raporu

**29 Ekim 2026 · Uygulama 0.7.0 · Analiz motoru 0.4.0**

Bu sprintin amacı simülasyonu değişken işletim koşullarına yaklaştırmak ve paneldeki boş tanıtım alanlarını ölçüm, deney ve inceleme içeriğiyle değerlendirmekti. Kapsamdaki geliştirmeler ve doğrulamalar tamamlandı. Gerçek saha doğruluğu iddiası yoktur.

## Yapılanlar ve gerekçeleri

### 1. Dinamik sentetik işletim

Önceki modelde yük yaklaşık sabit, ortam/nem sabit ve fanın tepkisi anlıktı. Yeni model, aynı 11 senaryoyu üç iş yükü profiliyle çalıştırır:

- **Sabit yük:** karşılaştırma için kararlı işletim ve küçük tohumlu dalgalanma.
- **Dalgalı yük:** 90 ve 23 saniyelik iki çevrim; ekipmanın değişken hesaplama yüküne verdiği tepkiyi gösterir.
- **Toplu işlem:** 120 saniyelik döngülerde kademeli yüklenme, 45 saniye tam yük artışı ve geri dönüş.

Temel IT yükü 2–8 kW, ortam 18–40 °C, fan zaman sabiti 1–20 saniye arasında ayarlanabilir. Ortam sıcaklığı yavaş değişir. Fan, soğutma ve giriş sensörü anında cevap vermez. Uygun arızalar 12 saniye içinde ilerler; eksik veri ve iletişim kaybı başlangıçta kesilir. Isıl atalet ve kW/kJ/s birim tutarlılığı korunur. Soğutma anlık hava akışı kapasitesiyle sınırlanır.

Böylece yalnızca düz çizgiler ve ani arıza sıçramaları yerine gecikme, yük döngüsü, toparlanma ve sıcaklık birikimi incelenebilir. Bu hâlâ tek bölgeli bir mühendislik modeli; tam veri merkezi, CFD veya saha kalibrasyonu değildir. Nem temsili sinyaldir; nem kütle dengesi yapılmaz. Ayrıntılı denklemler ve varsayımlar `SIMULATION.md` içindedir.

### 2. Deneyin tekrarlanabilir kaydı

Üretici sürümü, seçilen senaryo, koşullar, örnek sayısı, tohum ve başlangıç `generation` metadatasında saklanır. Arıza etiketi ve deney ayarları uzmanların `AnalysisRequest` girdisine eklenmez. Uzmanlar ölçümleri analiz eder; doğru cevabı deney etiketinden öğrenmez.

Aynı deney tanımı aynı ölçüm penceresini üretir. Replay ise ölçümleri yeniden üretmek yerine kaydedilmiş girdileri/politikayı/kaynakları yeniden analiz eder ve metadatayı korur. Önceki metadatasız kayıtlar desteklenir. Tanı algoritması değişmediği için analiz motoru 0.4.0 kaldı; uygulama sürümü 0.7.0 oldu. Eski referans üretici API ve CLI'de korunur; panelde dinamik model varsayılandır.

### 3. Daha dolu operasyon ve deney ekranı

Olay sayfasındaki tanıtım bloklarının yerine kayıtlı çalışma içeriği geldi:

- Seçili sayfaya ait kayıt, açık inceleme ve dikkat gerektiren sonuç sayıları.
- Soğutma → IT yükü → dönüş hattını gösteren şematik tesis görünümü; gerçek kayıttan sıcaklık, güç, fan, debi, ortam ve nem değerleri.
- Yan yana sıcaklık ve yük/soğutma grafikleri; telemetri ayrıntısında ayrıca fan komutu/geri bildirimi grafiği.
- Dinamik model seçimi, düzenlenebilir çalışma koşulları, senaryo brifingi ve planlanan zaman çizelgesi.
- Kayıtlı deney koşulları ve iletişim kesintisinde eski ölçüm uyarısı.

Boşluklar azaltıldı; kartlar, tablo ve sayfa aralıkları sıkılaştırıldı. Grafiklerin birimleri, çizgi stilleri ve erişilebilir başlıkları ayrı. Eksik değerler sıfıra çevrilmez; zaman boşluklarında çizgiler kesilir. Ekran canlı bağlantı izlenimi vermez. Sayaçlar veritabanı toplamı olarak sunulmaz.

## Testler ve sonuçların yorumu

- **435 Python testi geçti.** Önceki 364 teste 71 test eklendi. Ruff denetimi/biçimi temiz; satır ve dal birlikte kapsam **%97,85**.
- **39 arayüz testi geçti.** Önceki 31 teste 8 test eklendi. TypeScript, biçim kontrolü ve üretim derlemesi başarılı.
- **33 dinamik birleşim:** 11 senaryo × 3 yük profili. Kayıt, parametrelerden ölçümün yeniden üretilmesi, replay ve beklenen rapor/aday davranışı kontrol edildi. Normal örnekler `clear`; veri kesintileri `insufficient_data`; diğerleri `needs_review`. Beklenen nedenler aday listesinde; ek adaylar bulunabiliyor. Bu sonuç kesin teşhis oranı veya saha başarısı değildir.
- **Fiziksel hesap kontrolleri:** her adımın enerji dengesi, birinci dereceden tepkinin bağımsız hesabı, yük profilinin bilinen noktaları, kademeli fan arızası, eksik ölçüm, iletişim saatinin ilerlemesi, hatalı parametre ve 30/600 örnekte yüksek yük/ortam/gecikme sınırları.
- **Geriye uyumluluk:** Sprint 5 kaydı yeni metadata olmadan okunup aynı sonuçla yeniden analiz edildi; referans üretici varsayılan API davranışı korundu.
- **Gerçek HTTP ve temiz paket:** 22 referans + 33 dinamik birleşim, okuma/yazma yetkileri, katı istek sözleşmesi, durum geçişi, revizyon çakışması, replay, dört eşzamanlı kayıt ve panel dosyaları başarılı. Temiz ortam yalnızca kilitli çalışma bağımlılıklarını içerir; CLI de çalıştırıldı.
- **Tarayıcı:** WebKit'te farklı yük/ortam ayarlarıyla analiz, iletişim kaybında 240 saniye eskime uyarısı, üç grafik ve replay sonucu kontrol edildi. 375 px mobil, 812 px yatay ve 1440 px masaüstü düzenleri incelendi. Hata/uyarı konsol kaydı görülmedi; yeniden yükleme oturumu temizledi.

İlk testlerde yeni varsayılan ayarlara ait eski UI beklentileri güncellendi; test dosyası adı çakışması ve yeni testin veritabanı oluşturma ayarı düzeltildi. Görsel kontrolde tablodaki gizli erişilebilirlik etiketinin mobil yatay taşmaya neden olduğu bulundu; kaydırma alanına göre konumlandırılarak giderildi. Son doğrulamada başarısız test kalmadı. Bu ifade tüm olası hataların bulunmuş olduğu anlamına gelmez.

## Şu anda hangi parçalar tamamlandı?

- **L1/L2/L5:** tek bölgeli sanal tesis, gecikmeli kontrol/ekipman tepkisi, dinamik yükler, enerji dengesi, mevcut what-if ve model tutarlılığı araçları çalışıyor.
- **L3/L4:** sözleşmeler, yerel API, SQLite olay/çalışma/kanıt kayıtları, deney metadatası, revizyonlu inceleme ve replay çalışıyor.
- **L6:** Global Supervisor ve **12 deterministik uzman** çalışıyor; **36 kayıtlı rolün 24'ü planlı**. Bu sprint yeni uzman etkinleştirmedi.
- **L7:** CLI, API, operasyon görünümü, deney formu, rapor/telemetri/kanıt/ajan izi/geçmiş ve katalog kullanılabilir.

Çalışan uzmanlar: A02 sensör doğrulama, A03 sinyal analizi, A06 eksik veri; B02 anormallik, B03 neden adayları, B05 geçmiş eşleme, B06 hipotez eleştirisi; D02 simülasyon, D06 model doğrulama; F02 doküman erişimi, F03 kanıt doğrulama, F04 raporlama. D03 termal uzmanı, D04 enerji uzmanı ve D05 kalibrasyon uzmanı bu hesap araçları eklendi diye tamamlanmış sayılmaz. Tüm rollerin ayrıntısı `PROJECT_STATUS.md` içindedir.

## Korunanlar ve sınırlar

Önceki çalışma düzenleme öncesinde `work/sprint5-before-sprint6.zip` olarak saklandı. Git deposunda henüz commit yok; dosyalar önceki durumda olduğu gibi izlenmemiştir. Gerçek kullanıcı veritabanı yerine ayrı test veritabanları kullanıldı. Bağımlılık sürümleri değiştirilmedi; uygulama/panel sürümü yükseltildi. Derlenmiş paket eski panel varlıkları açısından kontrol edildi.

Gerçek PLC, şirket verisi, çoklu bölge, saha kalibrasyonu, ekipman elektrik tüketimi/PUE, bakım uzmanları, PLC kodu uzmanları ve doğal dil operatör asistanı henüz yok. 36 LLM çağrısı yapılmıyor; LLM çağrısı ve fiziksel kontrol komutu sıfır. Python 3.14.5 ve Node 20.20.2 ile doğrulandı; diğer Python sürümleri ve farklı tarayıcı motorları bu sprintte çalıştırılmadı.

## Sıradaki adım

Digital Twin Lab içinde aynı koşullardaki deneyleri yan yana karşılaştırmak: referans/dinamik model, normal/arıza ve farklı yük/gecikme ayarları. Sıcaklık tepe değeri, aralık üstünde geçen süre, yük/soğutma dengesi ve tanı farkları kayıtlı ölçümlerden hesaplanmalı. Parametre duyarlılığı ile sonuçların hangi varsayımlara bağlı olduğu görünür kılınmalı. Bundan sonra çok bölgeli modele geçişin kapsamı bu kanıtlarla seçilebilir.
