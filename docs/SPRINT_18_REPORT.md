# Sprint 18 — Operasyon arayüzünün görsel dönüşümü

2 Kasım 2026 · 0.17.0 aday sürümü · Motor 0.4.0

## İnceleme ve tasarım kararı

Kullanıcının sekiz referans ekranındaki ortak beklenti: koyu operasyon yüzeyleri,
net başlık/kart hiyerarşisi, tutarlı ikonlar, ölçüme bağlı grafikler ve görsel
inceleme alanları. Önceki panel uzun form/tablo düzeninde kaldı; operasyon
özetinin bulunmaması veriyi yorumlamayı zorlaştırdı.

Bu adım UI/UX Pro Max rehberiyle ortak koyu tasarım belirteçlerini, uygulama
kabuğunu ve işlevsel operasyon merkezini ekler. Referanslardaki finansal risk
metrikleri veya canlı ajan sayıları CanovaTwin'e taşınmadı.

## Uygulananlar

- Koyu lacivert yüzeyler, siyan grafik/vurgu rengi, mavi eylemler; tutarlı kart,
  form, tablo, durum, odak ve çizgi görünümü. Yeni ortak tema bütün sayfalara yüklenir.
- Sayısal menü işaretlerinin yerine yerel SVG ikonları; yeni varsayılan giriş
  `#/operations`. Eski sayfa adresleri ve karşılaştırma bağlantıları korunur.
- Operasyon merkezi: ekipman filosu, kayıtlı koşum sayıları, son olayların
  açık/kapalı dağılımı, 36 kayıtlı rolün uygulama haritası ve son kayıtlı pencere.
- Ekipman görselleri yerel SVG/CSS ile çizilir; bağımsız sanal hedefleri temsil
  eder. Fiziksel tesis bağlantısı veya çok kabinli topoloji iddiası yoktur.
- Ölçüm grafiklerinde seri açma/kapatma ve erişilebilir örnek seçimi vardır.
  Seçim saklanan örneğin zamanını/değerini gösterir; eksikler doldurulmaz.
- İstatistiklerin kapsamı görünür: katalogdaki ilk 10 ekipman ve son 10 olay.
  Ajan sayısı uygulama durumudur; canlı çalışan ajan sayısı değildir.
- Veri yokken sahte grafik yerine açık boş durum; istek hatasında tekrar deneme.

## Kontroller

629 Python / 65 panel testi geçti; satır+dal kapsamı %94,95. Ruff, Prettier,
TypeScript ve Vite üretim derlemesi temiz. Altı yeni test operasyon merkezi
boş/kayıtlı/gözlenen kimlik/hata durumlarını, grafik seri görünürlüğünü ve eksik okuma seçimini sınar.

Gerçek tarayıcıda okuyucu girişi, veriyle dolan operasyon kartları, kayıtlı
sıcaklık/güç grafikleri ve ölçüm seçimi kontrol edildi. 375 pikselde belge genişliği
375 piksel kaldı. Yeni bağımlılık veya dış font/görsel servisi eklenmedi.

Kurulu wheel/gerçek HTTP, paket dosyaları/lisansı, gizli bilgi ve mevcut güvenlik
CI denetimleri teslim kapısıdır. Bu değişiklik henüz birleştirilmemiş PR #41'in
üzerine ayrı commit olarak eklenir; PR başlığı/açıklaması son kapsamı temsil eder.
Bağımsız inceleme kuralı korunur.

## Sınırlar ve sonraki sıra

Bu teslim görsel dönüşümün operasyon merkezi ve ortak bileşen temelidir.
Tam proje veya saha ürünü tamamlandı anlamına gelmez. 12/36 uzman durumu,
çevrimdışı çalışma ve PLC erişim sınırı değişmedi. Bağımsız doğrulama,
kalibrasyon, kalan uzmanlar ve gerçek PLC entegrasyonu yol haritasında açıktır.

Sonraki ürün adımı: ekipman bazlı koşum seçicisi ve açık zaman ekseni kurallarıyla
karşılaştırmalı eğriler. Ardından kayıtlı kanıt/ajan izinin görsel bağımlılık
incelemesi; gerçek ilişki ve veri olmadan ilişki grafiği üretilmez.
