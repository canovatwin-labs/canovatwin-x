# Sprint 19 — Ekipman arşivi ve karşılaştırmalı eğriler

2 Kasım 2026 · Uygulama 0.18.0 · Analiz motoru 0.4.0

## Hedef ve yapılanlar

İş kaydı: [#42](https://github.com/canovatwin-labs/canovatwin-x/issues/42).
Ekipmandan koşum seçimiyle kimlik kopyalama gereksinimini kaldırmak ve iki
kayıtlı pencereyi açık zaman kurallarıyla aynı grafikte incelemek.

- `GET /api/v1/assets/runs?asset_id=...&limit=10&offset=0`, ekipmanın bütün
  olaylarındaki koşumları ve replay kayıtlarını en yeni kayıt sırasıyla listeler.
  SQL filtrelemesi sayfalama öncesindedir; kayıt JSON'ları topluca yüklenmez.
- Okuma yetkisi yeterli; bağlantı salt okunur, parametreler bağlanır. Limit 1–100,
  offset sıfır/pozitif. Bilinen boş ekipman boş liste, bilinmeyen kimlik 404 verir.
  Unicode ve eski gözlenen kimlikler korunur. API yolu sayısı 18 olur.
- Karşılaştırma ekranında ekipman ve koşum listeleri sayfalanır; kayıtlar temel
  veya aday olarak seçilir. Aynı kayıt iki tarafa seçilemez. Sayfa değişimi
  seçimleri korur; ekipman değişimi iki seçimi ve eski sonucu temizler.
- İstatistik sonucundan isteğe bağlı açılan eğriler yalnızca seçilen iki kaydı
  okur. Giriş sıcaklığı, IT yükü, termal soğutma gücü ve fan geri bildirimi için
  ortak x/y ölçeği, düz/kesikli çizgi ve erişilebilir açıklamalar kullanılır.
- Zaman ekseni her koşumun **ilk kaydedilmiş ölçümünden geçen saniyedir**;
  duvar saati veya arıza başlangıcı hizalaması değildir. Kayıp/boşluk/ters zaman
  çizgiyle birleştirilmez, yeniden örnekleme ve boşluk doldurma yapılmaz.
- Yanlış koşum kimliği/ekipman eşleşmesi ve gösterilemeyen sayısal grafik aralığı
  açıkça ele alınır. Grafiklerde nedensellik, tasarruf veya tanı başarısı puanı yoktur.

## Doğrulama

632 Python / 71 panel testi geçti. Python toplam satır+dal kapsamı %94,92;
Ruff, biçim, TypeScript ve üretim derlemesi temiz.

Üç yeni API testi: farklı olay/replay kayıtları, sayfa sırası, ekipman ayrımı,
boş/bilinmeyen kimlik, yetki, sayfalama sınırları, Unicode/SQL karakterleri ve
okuma sonrası değişmeyen geçmiş sayaçları. Altı yeni panel testi: listeden seçim,
eş seçim engeli/sayfalama, kanal değiştirme/eksik çizgiler, yanıt kimliği kontrolü,
saat farkına rağmen açık bağıl başlangıç ve eksik ölçüm üzerinden çizgi geçmeme.

Gerçek tarayıcıda okuyucu oturumuyla listeden iki farklı olayın koşumları seçildi;
sonuç ve termal güç eğrileri açıldı. Ekipman değişiminde seçimler temizlendi.
375 pikselde belge genişliği 375 piksel kaldı. Dar ekranda eğri kendi etiketli, klavyeyle kaydırılabilir bölgesinde okunur. İzole sentetik veritabanı kullanıldı.

Kurulu wheel/gerçek HTTP, güncel panel dosyaları ve MIT lisansı; tam bağımlılık
ve gizli bilgi denetimleri teslim kapısıdır. Uzaktaki Python 3.12/3.13/3.14 ve
bağımlılık denetiminin güncel sonucu PR Checks kaydında esas alınır.

## Korunanlar ve açık kapsam

Veritabanı şeması ve analiz motoru değişmedi; mevcut kayıt/replay yolu korundu.
Yeni bağımlılık, LLM çağrısı, fiziksel komut veya PLC bağlantısı yok.
12 uygulanmış / 36 kayıtlı uzman ayrımı değişmedi. Bu grafikler saha kalibrasyonu
veya bağımsız teşhis doğrulaması sayılmaz.

Koşum seçicisi yapılandırılmış ve gözlenen ekipmanları destekler. Sabit 10'luk
sayfalar var; arşiv sayfaları eşzamanlı yeni kayıtlara karşı dondurulmuş snapshot değildir. Arama, toplam sayfa sayısı, noktasal fark serisi, arıza başlangıcı
hizalaması ve grafik dışa aktarma henüz yok. Mevcut JSON dışa aktarma istatistik
sözleşmesini korur. Sonraki sıra kayıtlı kanıt ve ajan yürütme izinin görsel
bağımlılık incelemesidir; çıkarılmamış nedensel ilişki varmış gibi çizilmez.
