# Dinamik sentetik işletim modeli

Sprint 6 / uygulama 0.7.0, üretici `dynamic-1.0`. Mevcut referans üretici korunur. Panelde dinamik model varsayılandır; API'de `conditions` verilmezse eski referans üretici çalışır. CLI'nin mevcut senaryo komutları referans üreticiyi kullanmaya devam eder.

## Kapsam ve birimler

Model bir eşdeğer ısıl bölge ve soğutma ünitesidir. Örnekleme 1 saniye, pencere 30–600 örnektir. Referans sıcaklığı fiziksel durum değişkenidir; giriş sensörü 2 saniye zaman sabiti ve ±0,04 °C ölçüm gürültüsüyle bunu izler. Ölçülen sensör ile gerçek simülasyon durumu aynı şey değildir.

Enerji dengesi:

`T[k+1] = T[k] + (IT[k] + UA × (Tamb[k] - T[k]) - Qcool[k]) × dt / C`

`C=120 kJ/K`, `UA=0,1 kW/K`, `dt=1 sn`. Sıcaklıkta gizli kırpma yoktur. Her adımın enerji dengesi bağımsız hesapla test edilir. Nominal soğutma 10 kW, nominal debi 2,5 m³/sn'dir. Fan komutu hedef 23 °C'ye göre %20–100 aralığında oransaldır; komut doğrudan fiziksel cihaza gönderilmez.

Fan, birinci dereceden tepki kullanır: `y[k+1] = hedef + (y[k]-hedef) × exp(-dt/tau)`. Kullanıcı `tau` değerini 1–20 sn seçer; bu süre hedef değişiminin yaklaşık %63'üne ulaşma zamanıdır. Soğutma gücünün zaman sabiti 10 sn'dir ve anlık hava akışının taşıma kapasitesiyle sınırlıdır. Bu nedenle düşen debi, soğutmayı gecikme filtresinden önce sınırlayabilir.

## Çalışma koşulları

- Temel IT yükü 2–8 kW. Sabit profilde yalnızca ±0,04 kW tohumlu küçük yük değişimi bulunur.
- Dalgalı profilde temel yük, 90 sn ve 23 sn periyotlu %18 ve %6 genlikli iki bileşenle değişir.
- Toplu işlem profili 120 sn periyotludur. Artış 20–30 sn arasında yükselir; 30–75 sn arasında temel yükün %35 üzerinde kalır; 75–85 sn arasında geri iner.
- Temel ortam 18–40 °C; buna 600 sn periyotlu ±1,5 °C değişim eklenir. Bu, gün boyu hava durumu tahmini değil, kısa deney için reçete edilmiş sınır koşuludur.
- Nem %45 etrafında periyodik ve gürültülü temsili bir sinyaldir. Gizli ısı, yoğuşma veya nem kütle dengesi hesaplanmaz.

## Arızalar

11 senaryo korunur. Normal durumda arıza yoktur. Arızalar pencerenin üçte birinde başlar. Fan kaybı, sensör sapması, IT yük artışı, soğutma kaybı, hava akışı kısıtlaması, fan uyumsuzluğu ve birleşik arıza 12 sn içinde hedef şiddetine ilerler. Ekipman gecikmeleri bunun üzerine uygulanır. Eksik sensör ve iletişim kaybı başlangıçta kesilir; kontrol salınımı 10 sn periyotlu komuttur. İletişim kesildiğinde analiz saati ilerler; kısa deneylerde de en az 61 sn eskime oluşur.

Arıza etiketi uzmanlara verilmez. Kayıtta `generation` alanı senaryo, ayarlar, tohum, başlangıç, örnek sayısı ve üretici sürümünü saklar; `AnalysisRequest` yalnızca ölçümler ve analiz girdilerini içerir. Bu metadata olay kimliğini veya aday nedenleri belirlemez. Kaydın bütünlük özeti metadatayı da kapsar.

Aynı üretici sürümü + senaryo + ayarlar + tohum + başlangıç + sayı aynı ölçüm penceresini üretir. Yeni bir analiz önceki kayıtları araştırma girdisine ekleyebilir; bu nedenle veri üretimini tekrarlamak ile saklanmış analizi yeniden yürütmek ayrı işlemlerdir. Replay saklanmış ölçümleri/politikayı/kaynakları kullanır, metadatayı korur; ölçümleri yeniden üretmez. Eski metadatasız kayıtlar desteklenir.

## Doğrulamanın anlamı

Varsayılan 360 örnekte 11 senaryo × 3 profil kontrol edildi: normal örnekler `clear`; eksik sensör ve iletişim kesintileri `insufficient_data`; diğerleri `needs_review`. Beklenen neden veya birleşik arızanın bileşenleri aday listesinde yer alır. Ek adaylar bulunabilir; bu kontrol kesin teşhis doğruluğu, Top-3 başarı veya gerçek saha başarısı değildir. Modelin kendisiyle tutarlılığı saha validasyonu yerine geçmez.

CFD, birden fazla bölge, gerçek fan eğrileri, basınç ağı, chiller çevrimi, ekipman elektrik tüketimi/PUE ve saha kalibrasyonu henüz uygulanmadı. D03/D04/D05 rolleri bu model geliştirmesiyle etkinleşmiş sayılmaz.
