# Sprint 17 — Kayıtlı deney karşılaştırma paneli

2 Kasım 2026 · Uygulama 0.17.0 · Analiz motoru 0.4.0

## Hedef ve gerekçe

Sprint 16'nın salt okunur karşılaştırma sözleşmesini operatörün kullanabildiği
panel akışına bağlamak. İş kaydı: [#40](https://github.com/canovatwin-labs/canovatwin-x/issues/40).
Mevcut çalışmalar korundu; bu adım yeni uzman veya fiziksel bağlantı eklemez.

## Yapılanlar ve nedenleri

- `#/compare` ekranı, iki farklı kayıt kimliğini temel/aday olarak alır.
  Geçerli bağlantıda sonuç doğrudan açılır; okuma yetkisi yeterlidir.
- Olay ayrıntısındaki seçili koşum temel yapılabilir; geçmişteki başka bir koşum
  bağlantıyla aday seçilir. Aynı kayıt için karşılaştırma bağlantısı üretilmez.
- On bir kanalda ortalama, son okuma, minimum/maksimum, eksik/toplam sayıları
  ve aday − temel farkları yan yana görünür. Eksik değerler sıfıra çevrilmez.
- Ölçüm zamanı farkı, değişen girdiler, kaynak/motor, rapor durumu ve varsa
  aktarım sayaçları görünür. Değişim, otomatik iyileşme veya tasarruf sayılmaz.
- JSON indirme, `comparison-1.0` sözleşmesini iki koşum kimliği ve sınırlamalarıyla
  aynen korur. Oturum anahtarı dışa aktarılmaz; işlem geçmişe kayıt yazmaz.
- Geçersiz alan odaklanır ve hata ile ilişkilendirilir. Yüklenme, hata/yeniden
  deneme, boş seçim ve eski yanıtın seçim değişince elenmesi ele alındı.
  Tablolar etiketli ve klavyeyle kaydırılabilir; küçük ekranda sayfa taşmaz.
- Yarım sürüm güncellemesinde bağımlılık sürümünün de değiştiği yerel kilit
  dosyası temiz kurulumda yakalandı ve düzeltildi. Tüm bağımlılık kayıtları,
  URL ve hash'ler main ile eşit; yalnızca uygulama sürümü değişir.

## Doğrulama

- **629 Python / 59 panel testi geçti**; toplam Python satır+dal kapsamı **%94,95**.
  Ruff, biçim, TypeScript ve üretim derlemesi temiz.
- Dokuz yeni panel testi: okuyucu derin bağlantısı ve router, aynı/geçersiz
  kayıt seçimi, doğru alan odağı, eksik/minimum/maksimum değerler, hata/yeniden
  deneme, eski yanıt, gerçek JSON içeriği ve anahtarsız URL kodlaması,
  olay geçmişinde doğru temel/aday bağlantısı.
- Gerçek tarayıcı: izole sentetik veritabanıyla okuyucu girişi, normal/fan kaybı
  karşılaştırması, geçmişten replay/orijinal seçimi ve JSON indirme sınandı.
  İndirilen dosya Python sözleşmesiyle doğrulandı; aynı iki kayıt için hesaplanan
  yanıtla birebir eşleşti, 11 kanaldaki farklar sıfırdı ve geçmiş sayısı değişmedi.
- 375×812 dar ekran ve normal masaüstü görünümü kontrol edildi. Sayfa genişliği
  375 pikselde kaldı; geniş tablolar kendi bölgelerinde klavyeyle kaydırıldı.
- Kilitli temiz kurulum başarılı. Tam npm audit: 0 açık; Python geliştirme/runtime
  pip-audit: bilinen açık bulunmadı. Yeni bağımlılık veya güvenlik istisnası yok.
- Kaynak/wheel paketi, güncel panel dosyaları/MIT lisansı ve temiz ortama kurulu
  wheel üzerinden gerçek HTTP karşılaştırma, yetki, geçmiş ve replay kontrolleri
  bu teslimin paket kabul kapısıdır. GitHub'ın üç Python sürümü ve güvenlik
  kontrollerinin güncel sonuçları PR Checks kaydında izlenir.

## Durum ve sınırlar

L7 operatör paneli, L6 karşılaştırma/dışa aktarma akışına bağlandı. API yolu sayısı
17; analiz motoru ve veri şeması değişmedi. **12 uygulanmış / 36 kayıtlı uzman**
ayrımı korunur. Gerçek PLC, şirket verisi, saha kalibrasyonu ve tanı başarısı iddiası yok.

Bu ekran iki kayıt içindir. Farklı olaylardaki aynı ekipman koşumları kimlikleriyle
seçilebilir; bütün ekipman geçmişini tarayan görsel seçici henüz yok. Eğri bindirme,
zaman hizalama ve enerji/tasarruf hesabı eklenmedi. Karşılaştırma, test kapsamı
oranı veya sentetik sonuçlar bilimsel saha doğrulaması sayılmaz.

Sonraki adım: ekipmana bağlı, sayfalanmış koşum seçicisiyle kimlik kopyalama
zorunluluğunu kaldırmak; ardından açık zaman ekseni kurallarıyla eğri karşılaştırması.
Yeni commit/push mirackeser hesabından yapılır; ana dala geçiş diğer geliştirici
incelemesi ve mevcut kalite kapısına bağlıdır.
