# Yerel API — Sürüm 1

Uygulama 0.6.0, analiz motoru 0.4.0. HTTP katmanı önceki çekirdeği kullanır; algoritma değişmediği için eski 0.4.0 analizleri aynı motorla yeniden çalıştırılabilir.

## Kurulum ve başlatma

Proje klasöründe:

```sh
uv sync --locked --extra dev --no-editable
.venv/bin/canovatwin-api init
.venv/bin/canovatwin-api
```

İlk komut bağımlılıkları kurar. `init`, `.local/api-config.json` içinde iki farklı rastgele anahtar oluşturur; anahtarları terminale yazmaz ve mevcut dosyanın üzerine yazmaz. Dosya izinleri yalnızca sahibinin okuyup yazabileceği `0600` olarak ayarlanır. `.local/` Git dışında tutulur. Sunucu yalnızca `127.0.0.1:8000` üzerinde dinler; durdurmak için terminalde Ctrl+C kullanılır.

Canlılık: `http://127.0.0.1:8000/health`. OpenAPI sözleşmesi: `http://127.0.0.1:8000/openapi.json`. Bu iki uç anahtar istemez; analiz verisi veya yapılandırma döndürmez. Swagger/ReDoc için dış CDN varlıkları yüklenmez; bu sürümde tarayıcı tabanlı etkileşimli API konsolu yoktur. OpenAPI JSON çevrimdışı istemci geliştirme için kullanılabilir.

Farklı dosya için `canovatwin-api --config DOSYA`; ilk oluşturma için `canovatwin-api init --config DOSYA`. Veritabanı yolu göreliyse yapılandırma dosyasının bulunduğu klasöre göre çözülür. Varsayılan veritabanı `.local/history.sqlite3` olur; CLI ile aynı dosya kullanılabilir.

## Yetkiler

Korumalı istekte `Authorization: Bearer ANAHTAR` başlığı gerekir.

- `read_token`: katalog, olay, çalışma ve denetim geçmişini okur.
- `write_token`: okuma yanında analiz, replay ve durum değişimi yapar.

Yanlış/eksik anahtar 401, okuma anahtarıyla yazma 403 döndürür. Anahtar URL'ye, analiz girdisine veya tarayıcı kaynak koduna konulmamalıdır. Sunucu denetim kaydına `api-reader`/`api-writer` rolünü yazar; istemci `actor` alanı gönderemez. Bu, paylaşımlı yerel erişim yetkisidir; kurumsal kişisel hesap veya JWT oturumu değildir.

## Uçlar

- `GET /health`: servis canlılığı.
- `GET /api/v1/health`: yetkili veri deposu kontrolü; uygulama/motor sürümü ve 36/12 rol sayıları.
- `GET /api/v1/agents`: 36 rolün tanımı ve durumu.
- `GET /api/v1/incidents`: olay listesi; `status`, `limit`, `offset` filtreleri.
- `GET /api/v1/incidents/{incident_id}`: güncel durum, revizyon ve son çalışma özeti.
- `GET /api/v1/incidents/{incident_id}/runs`: çalışma özetleri.
- `GET /api/v1/incidents/{incident_id}/audit`: denetim geçmişi.
- `GET /api/v1/runs/{run_id}`: saklanan girdi, politika, sonuç ve kaynak snapshot'ları.
- `POST /api/v1/analyses`: açık JSON girdisini analiz edip kaydeder.
- `POST /api/v1/analyses/scenario`: sentetik senaryo üretir, analiz edip kaydeder.
- `POST /api/v1/incidents/{incident_id}/status`: gerekçeli, revizyon kontrollü durum değişimi.
- `POST /api/v1/runs/{run_id}/replay`: saklanan girdilerle yeni çalışma üretir.

Liste yanıtları `items`, `limit`, `offset` içerir. Limit 1–100, offset sıfır veya pozitif olmalıdır. Toplam kayıt sayısı bu sürümde dönmez; boş sonraki sayfa sayfalamanın bittiğini gösterir.

## İstek sözleşmeleri

Gövde `application/json` olmalıdır. Tarihler saat dilimli ISO 8601 dizgeleridir. Sayısal alanlarda metin/boolean gibi örtük dönüşümler kabul edilmez. Bilinmeyen alan, NaN/sonsuz, geçersiz kaynak ve yanlış şekil reddedilir. Çekirdek sözleşmeler gevşetilmeden JSON sınırında doğrulama yapılır.

Senaryo isteği örneği:

```json
{
  "scenario": "cooling_loss",
  "profile": "mvp12",
  "start": "2026-10-28T00:00:00Z",
  "count": 120,
  "seed": 42,
  "capture_history": true
}
```

`documents` verilmezse mvp12 demo notlarını kullanır. Verilirse en fazla sekiz dokümanlık açık snapshot dizisi kullanılır. `core6` ile doküman gönderilemez. `capture_history`, yalnızca üretilen senaryoda uygun eski kayıtların eklenmesini seçer.

`POST /analyses` gövdesi `{"request": ANALYSIS_REQUEST, "policy": OPTIONAL_POLICY}` biçimindedir. Girdideki araştırma kaynakları korunur; canlı geçmiş veya yeni doküman sessizce eklenmez. Politika verilmezse profilin varsayılanı kullanılır. Kısmi politika verilirse yalnızca açıkça gönderilen alanlar profil varsayılanını değiştirir; örneğin güncellik eşiği ayarı mvp12 bütçesini yanlışlıkla altı ajana düşürmez. HTTP yüzeyi dosya yolu veya PLC bağlantısı kabul etmez.

Durum değişim gövdesi:

```json
{"target": "investigating", "expected_revision": 1, "reason": "Sensör kayıtlarını incelemeye başladım"}
```

Son revizyon GET özetinden alınır. Yeni analiz veya başka karar revizyonu değiştirmişse 409 döner; güncel özet yeniden okunmalıdır. `open → investigating → closed`, `investigating → open` ve `closed → open` geçişleri desteklenir.

Replay boş gövde veya `{}` kabul eder. Kaydedilmiş girdi/politika kullanılır; eski kayıt korunur. Farklı motor sürümüyle replay 409 verir; kaydı okumak mümkündür.

## Sonuç ve hata anlamı

Analiz veya replay kaydı oluşturulduğunda HTTP 201 döner. Bu, fiziksel arızanın doğrulandığı veya analizin mutlaka tamamlandığı anlamına gelmez. `result.status` ayrıca incelenmelidir: kontrollü bütçe/kanıt engeli olan çalışma da tanı amacıyla kaydedilebilir. Replay için `matches` ve `differences` alanları sonuç karşılaştırmasını gösterir.

Uygulama hataları `request_id` ve `error` içerir. `error` içinde sabit kod, güvenli mesaj ve gerekirse alan sorunları bulunur. Ham istek, anahtar ve SQL metni hataya eklenmez. Yanıtlarda `X-Request-ID`, `Cache-Control: no-store` ve `nosniff` başlığı vardır.

Önemli HTTP durumları: 400 bozuk HTTP başlığı, 401 kimlik doğrulama, 403 yazma izni, 404 bulunamadı, 409 revizyon/geçiş/motor uyuşmazlığı, 413 büyük gövde, 415 yanlış içerik türü, 422 geçersiz sözleşme, 500 beklenmeyen hata, 503 depo kullanılamıyor. Kilitli depo için `Retry-After: 1` verilir. CORS preflight yanıtları CORS katmanının protokol yanıtlarıdır.

Gövde sınırı varsayılan ve üst sınır olarak 2 MB'dir; gerçek akan baytlar da kontrol edilir. Yapılandırmada daha küçük sınır seçilebilir. Her işlem kendi iş parçacığında açılıp kapanan SQLite bağlantısını kullanır. Sunucu startup sırasında depoyu doğrular; başka uygulamaya ait veritabanını dönüştürmez.

## Tarayıcı paneline hazırlık

`allowed_origins` varsayılan boş: CORS kapalıdır. Gelecek yerel panel için yapılandırmaya tam kaynak adresleri eklenebilir, örneğin `http://localhost:5173`. Joker, yol, kullanıcı bilgisi ve kontrol karakteri kabul edilmez. Çerez kimlik doğrulaması kullanılmaz; izinli tarayıcı isteği Authorization başlığını gönderir.

Bu sprint React ekranı, kişisel hesap/oturum sistemi, uzak dağıtım, TLS, görev kuyruğu veya üretim ölçeğinde hız sınırlama sağlamaz. Büyük ölçek veya şirket ağı kullanımı bu yerel prototip doğrulamasından çıkarılamaz.

## Doğrulama

```sh
.venv/bin/python scripts/check.py
.venv/bin/python scripts/smoke_api.py
```

İlk komut ağsız birim/entegrasyon testlerini çalıştırır. İkinci komut gerçek loopback HTTP gerektirir; geçici sunucu, yapılandırma ve veritabanı oluşturur, sonunda hepsini kapatıp temizler. Anahtarlar çıktıya yazılmaz.

## Yerel panel ve oturum — Sprint 5

`GET /api/v1/session`, geçerli anahtarın `role` ve `actor` bilgisini döndürür. Diğer korumalı uçlarla aynı kimlik doğrulamasını kullanır. Panel `/panel/` adresinden açılır; HTML kabuğu herkese açık, tüm veri ve yazma işlemleri korumalıdır. `/panel/assets/` yalnızca izinli derlenmiş dosyaları sunar. Ayrıntılar `PANEL.md` içinde. Motor 0.4.0 korunmuştur.

## Dinamik senaryo üretimi (0.7.0)

`POST /api/v1/analyses/scenario` gövdesine isteğe bağlı `conditions` eklenebilir: `{"workload":"cyclic","baseline_load_kw":4.2,"ambient_c":30,"fan_response_s":6}`. İş yükleri `steady/cyclic/batch`, yük 2–8 kW, ortam 18–40 °C, fan zaman sabiti 1–20 sn. Alan verilmez/null ise referans üretici korunur.

Yanıttaki isteğe bağlı `generation`, deney parametrelerini ajan girdilerinden ayrı saklar. Eski kayıtlar null olarak okunur. Replay metadatayı korur ve saklanmış ölçümleri kullanır. Ayrıntılar `SIMULATION.md` içinde.
