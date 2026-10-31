# CanovaTwin X — Sprint 10 sonuç raporu

**30 Ekim 2026 · Uygulama 0.11.0 · Analiz motoru 0.4.0**

## Neyi neden yaptık?

Önceki sprintler CSV dosyasını toplu doğruluyordu. Gerçek cihaz erişiminden önce
akışın zaman ve kesinti davranışını çevrimdışı sınayabilmek için `StreamCollector`
eklendi. Ölçüm zamanı ve geliş zamanı ayrıldı; sınırlı sıra bozulması olay
zamanına göre düzenleniyor. Geç/çift veri, tampon dolması ve saat hataları açık
hata üretiyor. Bağlantı ve tazelik ayrı raporlanıyor. Bu sınır, kayıp ölçümü
sessizce normal kabul etmeyi önler. Boş tamponda bile zaman eşiğinin ilerlemesi
kalıcı durum olarak tutulur; böylece geç kayıtlar sonradan içeri sızamaz.

## Kapsam

L3 telemetri katmanında bellek içi, tek varlıklı sentetik akış sözleşmesi var.
Son 600 kesinleşmiş ölçüm L4 kalite ve L6 analiz sözleşmesine pencere olarak
aktarılabilir; mevcut 12 uzmanın mantığı değiştirilmedi. 36 kayıtlı rolün 24'ü
hâlâ planlı. L1/L2 fiziksel model, L5 kayıt, L7 panel değişmedi.

Gerçek PLC, ağ protokolü, kalıcı olay günlüğü, şirket verisi ve dış veri kümesi
bu sprintte yok. Veri kökeni `synthetic`; dış veri doğrulama yolu atlanamaz.

## Test ve açık işler

Yedi yeni test olay zamanı sırası, geç/çift veri, dolu tampon, kopma/yeniden
bağlanma, saat hataları ve kesinleşmiş pencere davranışını denetler. Yerelde
**531 Python testi** ve **39 arayüz testi** geçti; Python satır+dal kapsamı
**%97,06**. Ruff, Prettier, TypeScript ve panel derlemesi temiz. Kaynak paketi
ve wheel üretildi; panel varlıkları ve MIT lisansı doğrulandı. Temiz geçici
ortama kurulan 0.11.0 wheel ile olay zamanı sıralaması, analiz penceresi ve
tazelik kontrolü geçti. Aynı kontrol CI kalite kapısına eklendi.

Sıradaki adım, bağımsız veri kümesinin lisans ve sensör anlamını yayıncıdan
doğrulamak; akış tarafında ise kalıcı olay günlüğü, yeniden başlatma ve kaynak
geri basıncı için ayrı kabul testleri eklemektir.
