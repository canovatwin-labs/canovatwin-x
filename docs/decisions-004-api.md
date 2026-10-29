# Karar 004 — Yerel, kimliği doğrulanan HTTP sınırı

28 Ekim 2026. Uygulama 0.5.0, analiz motoru 0.4.0.

API, mevcut HistoryService/SQLiteRepository üzerinde ince bir uygulama katmanıdır. Analiz algoritması, ajan sayısı ve veri deposu şeması değiştirilmedi. Bu nedenle ENGINE_VERSION artırılmadı; uygulama sürümüyle motor sürümü ayrı gösterilir. Motor sürümü uyumlu eski analizlerin replay davranışı korunur.

FastAPI app factory ve lifespan kullanıldı. İçe aktarma dosya veya veritabanı oluşturmaz; startup açıkça depoyu doğrular. Her senkron uç SQLite bağlantısını kendi fonksiyonu içinde açıp kapatır. Yield dependency ile bağlantıyı farklı thread'lere taşımak önlendi.

Katı çekirdek Pydantic modellerini gevşetmek yerine gövdeler sınırlı akıştan alınarak `model_validate_json` ile doğrulanır. Böylece JSON tarih/dizi gösterimleri desteklenirken sayısal tür, sonlu değer ve bilinmeyen alan kısıtları korunur. Aynı sözleşmeler OpenAPI bileşenleri olarak kaydedilir; testler bütün referansların çözüldüğünü denetler.

Okuma ve yazma anahtarları ayrı; actor istemciden alınmaz. Yapılandırma rastgele anahtarlarla, 0600 izinli ve yalnızca yeni dosya olarak üretilir. Bu yerel yetki modeli kişisel kurumsal hesap/oturum değildir. CORS açık kaynak listesiyle ve varsayılan kapalıdır. API kendiliğinden localhost dışına bağlanmaz.

Uygulama hataları güvenli JSON zarfı ve istek kimliğiyle döner. Erken gövde reddi ve beklenmeyen 500 yanıtlarında da izinli tarayıcının hata zarfını okuyabilmesi kontrol edildi. OpenAPI JSON yerel sunulur; dış CDN gerektiren dokümantasyon arayüzleri etkinleştirilmedi.

Geliştirme ortamında kurulu Starlette, eski HTTPX TestClient kullanımını kullanım dışı olarak bildirdi. Uyarı bastırılmadı; desteklenen HTTPX2 test istemcisine geçilip kilit güncellendi. Bu yalnızca geliştirme bağımlılığıdır; gerçek HTTP smoke testi standart kütüphane istemcisi kullanır.

Başvuru: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/), [lifespan testleri](https://fastapi.tiangolo.com/advanced/testing-events/), [HTTPBearer](https://fastapi.tiangolo.com/reference/security/), [CORS](https://fastapi.tiangolo.com/tutorial/cors/), [HTTPX2](https://pypi.org/project/httpx2/).
