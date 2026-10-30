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
