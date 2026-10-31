# Sprint 14 sonuç raporu — kayıtlı akış laboratuvarı

**31 Ekim 2026 · Uygulama 0.14.0 · Analiz motoru 0.4.0**

## Ne değişti, neden?

Önceki akış toplayıcısı ve günlük birer altyapı bileşeniydi. Operatör artık
fiziksel arızayı ve veri aktarım koşulunu ayrı seçerek kayıtlı bir deney
çalıştırabiliyor. Düzenli aktarım, gecikme/tekrar ve kesinti profilleri aynı
dinamik modele uygulanıyor. Gelen ölçümler sıraya alınıyor; geç ve tekrar
ölçümler gerekçeyle reddediliyor, kayıplar doldurulmuyor.

Yeni API yolu analiz edilen gerçek pencereyi, sanal saati, üretici reçetesini
ve tüm aktarım izini aynı SQLite çalışma kaydında saklıyor. Metadata uzman
girdilerine karışmıyor. Sayaçlar, olay sırası, kabul edilen örnekler ve SHA-256
iz parmak izi Pydantic tarafından denetleniyor. Kayıt yeniden açılabiliyor;
yeniden analiz aynı girdiyi ve deney metadatasını koruyor. Eski kayıtlarda yeni
alanın olmaması destekleniyor; SQLite şeması veya motor sürümü değiştirilmedi.

Panelde dördüncü çalışma alanı eklendi: deney formu, kalıcı sonuç bağlantısı,
kabul/ret/kayıp özeti, veri boşluklarını koruyan grafik, sanal bağlantı/tazelik,
filtreli ve sayfalanmış aktarım izi, reçete ve JSON indirme. Olay raporuyla iki
yönlü bağlantı kuruldu. Sonuç kaydedilirken çift gönderim önleniyor; başarısız
istekte form korunuyor; salt okunur oturum deney oluşturamıyor.

## Test ve gözlem

- Tam yerel kapı: **606 Python / 45 panel testi** geçti, Python satır+dal
  kapsamı **%94,91**. Ruff, Prettier, TypeScript ve Vite 8 derlemesi temiz.
- 11 fiziksel senaryo × 3 aktarım profili; 30/600 örnek sınırları, tekrar
  üretilebilir hash, geç/tekrar retleri, kesinti boşluğu, bozuk sayaç/hash,
  yetki, uygulamayı yeniden açma ve yeniden analiz sınandı.
- Tam npm audit: **sıfır bulgu**. Kaynak ve wheel paketleri oluşturuldu;
  paketli panel dosyaları kaynakla birebir eşleşti, MIT lisansı doğrulandı.
- Temiz kurulan 0.14.0 wheel, gerçek loopback HTTP üzerinde 22 referans ve
  33 dinamik birleşimi, üç aktarım profilini, kayıt/replay/yetki ve dört
  eşzamanlı yazmayı geçti. Kurulu pakette akış, günlük ve veri CLI yolları geçti.
- Tarayıcıda formdan kayda ve rapora geçiş, klavyeyle iz filtresi, JSON indirme,
  1440 px geniş, 375 px dar ve 812 px yatay düzen kontrol edildi. Dar/yatay
  sayfa genişliği viewport'u aşmadı. İndirilen JSON'un reçete, iz ve analiz
  penceresiyle tutarlı olduğu kontrol edildi.
- 120 örnek, tohum 42: kesintili aktarımda 100 kabul/20 düşen; gecikme/tekrarda
  63 kabul/65 ret elde edildi. Ret sayısı tekrar paketlerini içerir. Bu sayılar
  başarı puanı değildir. Eksik pencerelerde `insufficient_data` korunur.

Son commitin GitHub Python 3.12/3.13/3.14, panel, paket ve güvenlik sonuçları
PR'da izlenir. Geliştirici incelemesi tamamlanmadan ana dala alınmaz.

## Tamamlanan kapsam ve kalanlar

L3 çevrimdışı aktarım, L4 deney kaydı ve L7 operatör ekranı birlikte çalışır.
12 uygulanmış uzman ve 36 kayıtlı rol korunur; bu sprint yeni uzman eklemez.
Simülasyon sanal saatle hızlandırılmış tekrar yapar. Arka planda sürekli ağ
oturumu, gerçek PLC, çoklu varlık kataloğu, saha kalibrasyonu, diğer 24 uzman ve
bağımsız arıza teşhis performansı hâlâ açık kapsamdır. Tazelik kaydın sanal
saatine aittir; eski kaydın bugün açılması onu canlı ölçüm yapmaz.
