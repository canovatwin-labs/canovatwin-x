# Çevrimdışı telemetri akışı

`StreamCollector`, bir taşıma protokolü veya PLC bağlantısı değildir. Sentetik
`SensorSample` ölçümlerinin **ölçüm zamanı** ile **geliş zamanını** ayıran,
bellekte sınırlı bir sıralama sözleşmesidir. `append` kabul edilen örneği
tampona alır; `drain(as_of=...)` yalnızca gecikme eşiğinin gerisindeki örnekleri
zaman sırasıyla kesinleştirir. Boş bir `drain` çağrısı da zaman eşiğini ilerletir;
eşik geriye alınamaz ve sonradan gelen eski ölçüm reddedilir. `state` bu eşiği
`watermark_at` alanında görünür kılar. Tampon dolarsa çağıran açık hata alır; örnek
sessizce düşürülmez.

Geç gelen ölçüm, çift kimlik veya zaman damgası, geriye giden saat, aşırı gelecek
zamanı ve bağlantı kopukken veri reddedilir. `disconnect` ve `reconnect` açık
durum geçişleridir. `state` bağlantı ile ölçüm tazeliğini ayrı raporlar. `window`
yalnızca son 600 kesinleşmiş sentetik ölçümden mevcut `TelemetryWindow`
sözleşmesini üretir. Dış CSV için zorunlu manifest/doğrulama yolunu atlamaz.

`StreamCollector` tek başına bellek içindedir. Yeniden başlatmaya dayanıklı
çevrimdışı kayıt için ayrı [olay günlüğü](JOURNAL.md) kullanılır. Ağ geri
basıncı, birden çok varlık ve kopuş sırasında otomatik yeniden gönderim henüz
yoktur; bunlar ayrı kabul testleriyle eklenmeden canlı saha akışı olarak
sunulmaz.

## Kayıtlı aktarım deneyi

`run_stream_experiment(StreamRecipe(...))`, dinamik fiziksel modeli üç sürümlü
aktarım profiliyle çevrimdışı tekrarlar. `ordered` her ölçüme 200 ms gecikme
uygular. `jitter`, bağımsız tohumlu 0,1–6 sn gecikme ve 0,17,34… indekslerinde
tekrar gönderimi üretir. `outage`, planlanan sürenin üçte biri ile yarısı
arasında bağlantıyı keser; o aralıktaki ölçümleri doldurmadan düşen olarak izler.
Toplayıcının gecikme toleransı 2 sn, bu deneyin tazelik eşiği 10 sn'dir.
Fiziksel senaryonun iletişim kaybı, aktarım profilinin kesintisinden ayrıdır.

Bu hızlı, sanal saatli deney yeni bir canlı oturum açmaz. Her olayın sanal
geliş/ölçüm saati, kabul/ret kodu ve bağlantı/tazelik durumu kaydedilir. Son
tampon kesinleştirildikten sonra yalnızca kabul edilen sıralı pencere analiz
edilir. Üçten az ölçüm kalırsa kayıt oluşturulmadan 422 döner.

API örneği (`POST /api/v1/analyses/stream`, yazma anahtarı gerekir):

```json
{"scenario":"fan_loss","delivery":"outage","count":120,"seed":42,"start":"2026-10-31T00:00:00Z","profile":"mvp12","conditions":{"workload":"cyclic"}}
```

`RecordedAnalysis.stream_experiment`, reçete, tüm aktarım izi, sayaçlar, son
durum, analiz penceresi ve SHA-256 iz parmak izini taşır. Bunlar uzman girdisi
olan `AnalysisRequest` içine konmaz. Pydantic sayacı, kabul edilen örnekleri,
olay sırasını, son saati ve parmak izini denetler; kayıtlı pencere ve analiz
saati metadatayla eşleşmelidir. SQLite kaydı yeniden açıldığında alan korunur;
eski kayıtlarda varsayılan `null` kabul edilir. Yeniden analiz aynı metadatayı
korur; aktarımı yeniden üretmek için sürümlü reçete ayrı çalıştırılır.

Ret sayısı tekrar paketlerini de içerir; `üretilen - ret` kayıp ölçüm sayısı
değildir. Düşen ölçümün kaynak saati yalnızca bu simülasyonda bilinir. İz hash'i
imzalı saldırı kanıtı değildir. Aynı üretici ve Python/bağımlılık ortamında
reçete tekrarlandığında iz ve pencere aynı kalır; saha ağının veya fiziksel
tesisin doğruluğunu kanıtlamaz.
