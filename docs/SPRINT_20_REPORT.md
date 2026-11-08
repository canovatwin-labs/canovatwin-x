# Sprint 20 — Kayıtlı kanıt ve ajan incelemesi

8 Kasım 2026 · Uygulama 0.19.0 · Motor 0.4.0

## Yapılanlar ve gerekçesi

Raporun dayandığı ölçümlere ulaşmak için kimlik kopyalama ihtiyacı kaldırıldı.
Rapor bağlantısı seçilen kanıtın sayfasını açar; üretici filtresi ve metrik/kimlik
araması ile kayıtlar daraltılır. Kaynak ölçümler 10'luk sayfalarda, ham değerleriyle
incelenir. Üreticinin ajan izine ve oradan kanıta geri geçilebilir. Sekme odağı
korunur; koşum değiştiğinde eski seçimin başka kayda taşınması engellenir.

Rapordaki genel kaynak, gözlem, destek ve karşı kanıt referansları ayrı gösterilir.
Eksik veya yinelenen kaynak kimliği için değer seçilmez. Ajan çıktısı hem görev
hem ajan kimliğiyle eşleştirilir. Başarısız adım ve çıktısız çalışma görünürdür.
Süre çubukları en uzun adıma göre ölçeklenir; kayıt dizisi sırası başlangıç zamanı,
paralellik veya görev bağımlılığı olarak yorumlanmaz. Kanıt üreticiye bağlanır;
belirli görev çağrısına atıf için veri sözleşmesinde bilgi yoktur.

## Doğrulama

- 632 Python testi geçti; satır+dal kapsamı %94,92.
- 82 panel testi geçti. 11 yeni test: rapor/destek/karşı kanıt bağları,
  filtre/sayfa/klavye, eksik ve çift kimlikler, engellenmiş/boş kayıtlar,
  güvenli metin gösterimi, tam ajan+görev eşleşmesi, sıfır süre, okuyucu geçişleri
  ve koşum değişiminde seçim temizliği.
- Ruff, biçim, TypeScript ve üretim derlemesi geçti.
- Temiz ortama kurulu wheel ile gerçek HTTP: 22 referans + 33 dinamik birleşim,
  üç aktarım profili, yetki, geçmiş, yaşam döngüsü, replay ve eşzamanlı yazma geçti.
- Wheel güncel dört panel dosyası ve MIT lisansıyla doğrulandı.
- Python geliştirme/çalışma bağımlılıkları ve npm kilidi tarandı: bilinen açık yok.
- Gerçek tarayıcıda ayrı sentetik veritabanı ve okuyucu oturumuyla rapor → kanıt
  → üretici akışı doğrulandı. Son pakette bağlantının doğru sayfayı açması ve
  ayrıntı odağı/görünür konumu kontrol edildi. Bu sprintte mobil gerçek tarayıcı
  kontrolü yapılmadı; dar ekran stilleri üretildi, önceki mobil kabulün yerine geçmez.

## Tamamlanma ve kalan kapsam

Bu adım yerel kanıt inceleme iş akışını tamamlar. 12 / 36 uzman uygulanmış
(%33,3 rol oranı); 24 rol planlıdır. Bu oran toplam ürün tamamlanması değildir.
Yedi katmanın mevcut durumu PROJECT_STATUS.md içinde tek tek kayıtlıdır.
Çevrimdışı senaryo → analiz → kayıt → rapor → kanıt → replay/karşılaştırma yolu
çalışır. Bağımsız etiketli saha değerlendirmesi, fiziksel kalibrasyon, sürekli
endüstriyel bağlantı, sanal kontrolör durum makinesi, koordinatörler/kalan uzmanlar,
semantik bilgi erişimi ve üretim işletimi açık kapsamdır.

Yeni bağımlılık veya veritabanı göçü yok. Motor ve fiziksel komut sınırı korunur.
Sonraki operatör adımı, kanıtın kaynak ölçümlerini zaman grafiğinde vurgulamaktır.
Sprint 19 PR #43 henüz inceleme beklediğinden bu adım onun üzerine ayrı dalda
hazırlanmıştır. Ana dala alınma ve uzak kalite sonucu PR kaydından izlenmelidir.
