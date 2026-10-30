# CanovaTwin X — Sprint 9 sonuç raporu

**30 Ekim 2026 · Uygulama 0.10.0 · Analiz motoru 0.4.0**

Sprint 8 dış CSV dosyalarının yapısını ve köken beyanını doğruluyordu. Bu sprint,
kontrolden geçen sınırlı bir ölçüm penceresini mevcut deterministik uzmanlara
keşif amaçlı sunar. Gerçek üçüncü taraf veri seti, şirket verisi veya saha
etiketi eklenmedi.

## Yapılanlar ve gerekçeleri

1. **Doğrulama sonrası pencere:** Bütün manifest parçaları kontrol edilir,
   seçilen dosyanın hash'i yeniden okunur ve 3–600 satırlık pencere oluşturulur.
   Birimler normalize edilir; eşlenmemiş kanallar `null` kalır. Eksik kanal
   arıza etiketi veya tahmini veriyle doldurulmaz.
2. **Açık köken:** Pencere `declared_external`, ölçümlerden türetilen kanıtlar
   `declared_external`, çalışma `external_review` olarak işaretlenir. Çıktı
   manifest/dosya/girdi hash'lerini, kaynak ve lisans beyanını ve satır seçimini
   içerir. Kaynak/lisans yalnızca beyan edilmiştir; etiket durumu `unknown`.
3. **Temkinli rapor:** Eksik kanallar mevcut veri kalitesi kapısında güvenli
   çekimserliğe yol açar. Bütün kanallar bulunsa ve örnek kurallar `clear`
   döndürse bile insan incelemesi zorunludur. Rapor saha eşiği ve sensör
   anlamının doğrulanmadığını söyler. Yalnızca `core6` kullanılır; sabit demo
   dokümanları dış veriye kanıt olarak eklenmez.
4. **Yüzey sınırı:** Genel HTTP analiz yolu doğrudan dış kaynak iddiasını 422
   ile reddeder. Dış inceleme ayrı çevrimdışı CLI seçeneğinden geçer; geçmiş
   veritabanına yazılmaz, fiziksel kontrol komutu üretilmez.

## Testler ve yorum

- **524 Python testi** ve **39 arayüz testi** geçti; Ruff/Prettier, TypeScript
  ve üretim derlemesi temiz. Python satır+dal kapsamı **%97,20**. Yeni testler
  eksik kanalda çekimserliği, tam kanalda zorunlu insan incelemesini, dış kanıt
  kökenini, doğrudan API sınırını, pencere hatalarını ve CLI dosya davranışını
  kontrol eder.
- Kurulu paketle geçici üç parçalı yerel CSV üzerinden içe alma ve dış inceleme
  çalıştı. Bu örnek gerçek veri seti değildir ve teşhis başarısı ölçmez.
- Önceki sentetik testler ve 66 yöntem/vaka değerlendirmesi korunur. Motor
  sürümü 0.4.0 kaldı; eski sentetik kayıtların sonuç anlamı değişmedi.
- GitHub CI'de Python 3.12, 3.13 ve 3.14 kalite işleri ile bağımlılık denetimi
  geçti. Kaynak paketi, wheel, panel ve MIT lisans kontrolü; kurulu paketle gerçek
  yerel HTTP, yetki, replay ve dört eşzamanlı yazma kontrolü de bu kapıda geçti.

## Katmanlar ve açık işler

L3/L4 doğrulanmış dış veriden sınırlı pencere oluşturabiliyor. L6 mevcut altı
uzmanı bu pencerede çalıştırıyor; **36 kayıtlı rolün 12'si uygulanmış**, 24'ü
planlı. L1/L2/L5'in tek bölgeli sentetik modeli ve L7 paneli değişmedi.
Gerçek PLC, saha kalibrasyonu, üretim güvenliği, doğal dil operatör asistanı ve
LLM çağrıları bu sprintin parçası değil.

Sıradaki iş, yayıncı lisansı ve sensör semantiği elle incelenmiş bağımsız bir
HVAC/soğutma veri kümesini bu protokole uyarlamak. Arıza etiketleri gerçekten
mevcutsa ekipman ve zaman ayrımlı hata analizi yapılabilir; yoksa bu keşif
çıktılarına F1 veya saha teşhis doğruluğu atanmamalı. Sürekli akış, gerçek
gateway, kalibrasyon ve Digital Twin Lab sonraki aşamalardır.
