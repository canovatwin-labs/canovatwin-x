# Karar 002 — Önce çevrimdışı kalıcı kayıt

28 Ekim 2026, Sprint 2.

Başlangıç taslağı PostgreSQL öngörüyor. Yerel, tek geliştiricili ve çevrimdışı çekirdekte önce kayıt sözleşmelerini ve veri bütünlüğünü doğrulamak için Python standart kütüphanesindeki SQLite seçildi. Yeni üçüncü taraf bağımlılık eklenmedi.

`AnalysisRepository` analiz hizmetinin depodan beklediği işlemleri tanımlar. SQLite bağlantısı ajanlara verilmez; kaydetme ve yaşam döngüsü işlemleri uygulama katmanında kalır. PostgreSQL adaptörü bu arayüzü uygulayabilir; SQLite SQL'i taşınabilir SQL kabul edilmez. İleride gerçek adaptör, migration ve eşzamanlılık testleri ayrıca gerekir.

`RecordedAnalysis` girdi/politika/sonuç/versiyon/kayıt zamanı/kullanıcı etiketi taşır. `AnalysisRun` ve mevcut analiz JSON sözleşmesi korunmuştur. Sadece kalıcı kayıt seçeneğiyle dış nesne `RecordedAnalysis` olur. `run_id` UUID tabanlı, `incident_id` mevcut girdi+politika özeti tabanlıdır.

Tek JSON kaydı inceleme ve yeniden çalıştırma için tam anlık görüntüdür. Kanıt ve ajan izleri ayrıca run kimliğiyle ayrılmış tablolara yazılır. Her ikisi tek transaction içinde tutulur; ayrıntı okumasında iki gösterimin tutarlılığı kontrol edilir. Kalıcı hipotez/rapor ayrı tablolara gereksiz çoğaltılmaz; anlık görüntü içindedir.

Saklanan girdi ve politika değiştirilemez; inceleme durumu revizyon denetimiyle değişebilir. Yeni analiz de revizyonu ilerletir; eski analiz üzerine verilmek üzere hazırlanmış durum kararları böylece fark edilir.

Motor sürümü uyuşmayan geçmişi tekrar çalıştırma reddedilir. Karşılaştırma yalnızca çalışma sürelerini dışarıda bırakır. Fiziksel model doğruluğu veya akademik başarım ölçümü bu özelliğin sonucu değildir.
