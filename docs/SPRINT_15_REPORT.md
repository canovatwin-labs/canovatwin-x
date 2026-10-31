# Sprint 15 sonuç raporu — varlık kataloğu ve ekipman inceleme alanı

**31 Ekim 2026 · Uygulama 0.15.0 · Motor 0.4.0**

## Yapılan iş ve gerekçe

Akış laboratuvarının ardından yol haritasındaki varlık/etiket kataloğu ve
ekipman bazlı operatör akışı uygulandı. Yapılandırılmış iki sentetik ünite ve
geçmişte gözlenen diğer kimlikler ayrılıyor. Her ekipman için gerçek kayıtların
olay/inceleme/çalışma sayısı, son pencere, 11 sensörün birimi ve kalite aralığı,
son değer/eksik sayısı ve filtrelenmiş olay geçmişi gösteriliyor.

Senaryo ve aktarım formları seçilen ekipmanı ve önerilen işletim koşullarını
alıyor. Üretim metadatası, pencere, akış yapılandırması ve kaydedilen analiz
aynı kimliği koruyor. API yapılandırılmış hedefleri doğruluyor; tanımdan çıkarılan
kimliğin geçmişi korunurken yeni hazır deneyleri engelliyor. SQLite şeması
değişmedi; eski yapılandırmalar ve gerçek 0.14 akış JSON çıktısı yüklenebildi.

Geçmiş vaka sorgusunda yeni çoklu ekipman kullanımının açığa çıkardığı bir
sınır durumu düzeltildi: başka ekipmanların son 100 olayı, ilgili eski vakayı
dışlayabiliyordu. Süzme sayfalamadan önce yapılıyor. 101 farklı ekipmanla
oluşturulan kalıcı veri üzerinde regresyon testi bunu doğruladı.

## Doğrulama

- Tam yerel kapı: **618 Python / 50 panel testi**, Python satır+dal kapsamı
  **%94,86**. Ruff, Prettier, TypeScript, API şema üretimi ve Vite 8 derlemesi temiz.
- Hedef ayrımı, varsayılan/özel koşul birleştirme, kayıt/replay, katalogdan
  çıkarma sonrası yeniden açma, sayfalama, eski parmak izi, yetki, bilinmeyen
  hedef reddi ve SQL/Unicode karakterli kimlikler sınandı.
- Panel testleri hedef seçimini, tanımsız hedefte işlemi engellemeyi, eksik son
  değeri korumayı ve kimliklerin güvenli URL kodlamasını doğruladı.
- Temiz kurulan 0.15.0 wheel, gerçek HTTP üzerinde önceki 22 referans / 33
  dinamik birleşimi ve üç aktarım profilini; ayrıca ikinci ekipman, sayaçlar,
  filtreli geçmiş, replay ve bilinmeyen hedef reddini geçti. Paket paneli
  kaynakla birebir ve MIT lisansı tutarlı.
- Tarayıcıda boş katalog → ikinci ünite → ekipman varsayılanıyla analiz → rapor
  → ekipman akışı geçti. İkinci ünitede bir olay varken birincisi sıfır kaldı.
  1440 px görünüm ve 375 px dar sayfada katalog/ayrıntı düzeni kontrol edildi;
  dar sayfa viewport genişliğini aşmadı.
- Tam npm audit sıfır bulgu verdi. Python kilit dosyasının geliştirme araçları
  dahil pip-audit denetiminde bilinen zafiyet bulunmadı. Son commitin GitHub
  kontrolleri PR'da ayrıca izlenir. GitHub'ın eski #1 uyarısı kaldırılmış
  minimatch 5.1.9 içindi: `main` 9b2182e kilit dosyasında ve güncel 187 paketlik
  GitHub SBOM'da bu paket yok. Kayıt bu kanıtlar yorumuna eklenerek `not_used`
  gerekçesiyle sınıflandırıldı; açık uyarı listesi boş döndü. Güvenlik taraması,
  zamanlanmış denetimler ve kontrol eşikleri değiştirilmedi.

## Tamamlanan katmanlar ve açık kapsam

L3'te ekipman ve ölçüm sözleşmesi; L4'te ekipman bazlı geçmiş sorgusu ve geriye
uyumluluk; L7'de katalog/inceleme alanı tamamlandı. 12 uygulanmış / 36 kayıtlı
uzman korunuyor; bu sprint yeni ajan eklemiyor. Ayrıntılar: [ASSETS.md](ASSETS.md).

Üniteler aynı tek bölgeli modelin bağımsız koşumlarıdır; bağlı bir tesisin
çok bölgeli fiziği değildir. Panelden katalog düzenleme, ekipman metadata
değişikliği denetim geçmişi, fiziksel etiket keşfi, PLC/gateway, saha kalibrasyonu
ve kalan 24 rol hâlâ açık kapsamdır. Sıradaki ürün adımı kayıtlı deneyleri aynı
ölçütlerle yan yana karşılaştırmaktır.
