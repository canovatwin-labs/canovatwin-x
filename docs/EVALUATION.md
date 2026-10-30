# Çevrimdışı deney ve değerlendirme protokolü

Bu modül tek bir manifestte tanımlanan sentetik vakaları üç deterministik
yöntemle karşılaştırır. LLM, eğitim servisi, şirket verisi veya PLC kullanmaz.

## Çalıştırma

```sh
uv sync --locked --extra dev --no-editable
.venv/bin/canovatwin-evaluate run examples/evaluation/synthetic-v1.json --split test --output-dir .local/evaluation/run-001
```

Özel bir başlangıç dosyası oluşturmak için:

```sh
.venv/bin/canovatwin-evaluate template --output experiment.json
```

Örnek manifest 66 vaka içerir: her split için 11 senaryo × 2 işletim/enjeksiyon
koşulu. `test` seçimi 22 vaka × 3 yöntem = 66 yürütmedir. `train` ve `validation`
ayrı komutlarla seçilebilir; bunlar otomatik eğitim veya eşik ayarlama yapmaz.

Çıkış kodları: 0 yürütme tamamlandı; 1 en az bir çalışma bloke oldu (rapor yine
üretilir); 2 giriş/dosya hatası. Düşük teşhis puanı işlem hatası değildir.

## Manifest ve izolasyon

`schema_version=1.0`, `generator_version=evaluation-1.0`, kaynak ve MIT lisansı,
veri kümesi kimliği ve vaka listesi kaydedilir. Her vaka split, tarafsız case_id,
senaryo, seed, başlangıç, örnek sayısı, işletim koşulları ve enjeksiyon ayarları taşır.

- Train/validation/test seed kümeleri ayrıdır. Aynı seed bir split içinde farklı
  senaryolarda kullanılabilir; başka split'e geçemez.
- Yinelenen vaka kimlikleri ve aynı üretim yapılandırması reddedilir.
- Değerlendirmeden önce bütün split'ler üretilip telemetri içerikleri karşılaştırılır.
  Kimlik veya mutlak tarih değiştirerek aynı seriyi başka kümeye kopyalamak reddedilir.
- Uzmanlara yalnızca `AnalysisRequest` içindeki telemetri ve inceleme saati ulaşır.
  Senaryo, gerçek etiket, seed, split ve enjeksiyon parametreleri aktarılmaz.
- mvp12 sabit demo notları kullanır; train/validation/test vakaları geçmiş eşleme
  girdisine veya belge kaynağına taşınmaz. Otomatik optimizasyon yapılmaz.
- Manifest en fazla 2 MB, 300 vaka; vaka 60–600 örnektir. Bu sınırlar kaynak
  kullanımını sınırlar, harici/güvenilmeyen kod için süreç izolasyonu sağlamaz.

## Enjeksiyonlar

- `onset_fraction`: pencerenin 0,10–0,85 aralığında arıza başlangıcı.
- `severity`: 0,25–1,00; fan/soğutma kaybı, yük, sensör bias ve salınım şiddeti.
- `sensor_noise_c`: giriş sensöründe ±0–0,5 °C tekdüze gürültü.
- `missing_fraction`: yalnızca sensor_missing senaryosunda, başlangıç sonrası
  her giriş sıcaklığı örneğinin kayıp olma olasılığı (0,20–1,00).

Kayıp sensör için ayrı rastgele sayı akışı kullanılır; eksik ölçüm oranı fiziksel
IT yükünü veya termal yörüngeyi değiştirmez. `dynamic-1.0` API/panel üretimi eski
çıktısıyla birebir korunur; 33 tarihsel senaryo/profil checksum testi bunu denetler.
Haberleşme kaybında eski modelin en az 61 saniye gözlem gecikmesi varsayımı sürer.

## Yöntemler

- `threshold`: ajan araçları veya supervisor kullanmayan basit eşik karşılaştırıcısı.
  Sensör ayrışması 2 °C, yük artışı 2 kW, fan farkı 15 yüzde puan, debi/kapasite
  oranı 0,65; yüksek sıcaklık 27 °C. Kayıp oranı %20 ve eskilik 60 saniye.
  Bu değerler demo başlangıcıdır, test kümesine göre ayarlanmaz.
- `core6`: mevcut altı uzmanlı yönlendirme.
- `mvp12`: mevcut on iki uzmanlı akış; sabit yerel notlar, eleştiri ve what-if.

Basit eşik yöntemi klasik ML modeli değildir. Tek LLM/6/12/24/36 mimarilerinin
akademik deneyleri ve eğitimli modeller sonraki çalışmalardır.

## Metrikler ve paydalar

Alarm pozitifliği `needs_review` veya `insufficient_data` sonucudur. Ground truth
normal senaryoda boş, diğerlerinde arıza etiketleridir. Birleşik arıza, fan kaybı
ve soğutma kaybı olarak iki ilkel etikete açılır. Yöntemlere doğru cevap verilmez.

- Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN).
- Yanlış alarm = FP/(FP+TN); örnek manifestte yalnızca iki normal test vakası
  vardır. Sıfır yanlış alarm genellenebilir sıfır risk iddiası değildir.
- Adaylar çok etiketli değerlendirilir. Macro F1, gerçek veya tahmin desteği olan
  etiketlerin F1 ortalamasıdır; hiç görülmeyen etiketler ortalamaya girmez.
- Top-3, arızalı vaka başına ilk üç adayda kapsanan gerçek etiket payının
  ortalamasıdır. Mevcut kural sırası kullanılır; olasılığa göre sıralama değildir.
- `blocked` kayıtlar kaybolmaz: toplam, skorlanan, bloke sayıları ve coverage
  raporlanır. Sınıflandırma puanları yalnızca tamamlanan çalışmalara koşulludur.
  Daha yüksek F1 fakat düşük coverage daha iyi yöntem kanıtı değildir.
- `insufficient_data` başarılı güvenli çekimserliktir; alarm sayılır. Hipotez
  üretilmezse aday recall'ına katkı yapmaz; hata veya kök neden başarısı sayılmaz.
- p50/p95, sıralı sürelerde doğrusal ara değer hesabıdır; aynı makinede tek koşu
  gözlemidir. Ortalama aktif rol sayısı yalnızca tamamlanan rolleri sayar.
- Kanıt kapısı oranı mevcut iç denetimin geçtiğini gösterir; bağımsız kaynak
  doğruluğu ölçümü değildir. Baseline için uygulanamaz (`null`).
- MAE/RMSE yalnızca model ölçümü olan tamamlanmış mvp12 vakalarında ortalanır;
  örnek sayısı ayrıca verilir. Modelin kendi üreticisindeki öz-tutarlılığıdır.
- Paydası olmayan oranlar 0 veya 1 uydurmak yerine `null`/`n/a` olur.

## Çıktılar

Yeni klasörde `manifest.json`, `report.json`, `cases.csv`, `summary.md` oluşur.
Var olan klasör veya manifestin üzerine yazılmaz. Disk hatasında kısmi çıktı
oluşabilir; komut hata döndürür ve bu klasör tamamlanmış koşu olarak kullanılmaz.

Manifest, kaynak Python dosyaları ve teknik sonuçlar için SHA-256 kaydedilir.
`result_sha256` süreleri dışarıda bırakır; aynı kod/girdi/çalışma ortamında tekrar
karşılaştırması içindir. CSV bütün vaka/yöntem sonuçlarını, blokaj kodlarını ve
telemetri girdi hash'lerini taşır. Ham şirket verisi aktarımı bu protokolde yoktur.

## Sınırlar ve sonraki doğrulama

Ayrı seed, bağımsız saha verisi değildir. Üretici ile analiz aynı projeden gelir;
normal/arıza çeşitliliği sınırlıdır, test kümesi küçüktür. Başarı için keyfi F1
barajı belirlenmedi. Açık veri uyarlama, izin/lisans manifesti, zaman/ekipman
ayrımı, daha geniş seed kümeleri, güven aralıkları, eğitimli baz modeller ve
mimari ablation deneyleri yol haritasında açık kalır. Test kümesi sonuçlarına
bakılarak eşiğin tekrar ayarlanması bu raporu bir doğrulama raporuna dönüştürmez.
