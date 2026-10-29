# Sprint 1 kapanış raporu — Özgün mimariye uyarlama

**Tarih:** 28 Ekim 2026  
**Sürüm:** 0.2.0  
**Sonuç:** İlk altı uzmanı içeren çevrimdışı çekirdeğin kabul ölçütleri tamamlandı.

Bu rapor, önceki ilk taslağın “sprint tamamlandı” değerlendirmesini özgün belgelerdeki kapsamla düzelterek kapatır. 12 ajanlı MVP veya bütün platform tamamlanmış değildir.

## 1. Çalışma konumu ve koruma

Sohbetin proje alanına alınması kaynak dosyaları taşımamıştı. Önceki 13 proje dosyasını koruyarak mevcut proje alanındaki `canovatwin-x` klasörüne çalışma kopyası oluşturuldu. Eski kaynaklar yerinde bırakıldı; ayrıca proje alanının `work/canovatwin-bootstrap-backup.zip` dosyasında ilk taslak yedeklendi. Önceki depoda commit bulunmuyordu; kaybolan commit geçmişi yoktur.

Yeni çalışma konumu: `/Users/mirackeser/Documents/ChatGPT/PLC Canovate/canovatwin-x`.

## 2. Yapılan işler ve gerekçeleri

### Özgün ajan kataloğu

A01–F06 arasındaki 36 rol kaynak belgelere göre kaydedildi. İlk altı rol A02 Sensor Validator, A03 Signal Analyzer, B02 Anomaly Investigator, B03 Root Cause Analyst, F03 Evidence Verifier ve F04 Report Composer olarak düzeltildi. Bu değişiklik önceki sıcaklık/nem odaklı rol listesini özgün teşhis mimarisiyle uyumlu hale getirdi.

Her rolün amacı, grubu, sürümü, durumu, araç izinleri ve giriş/çıkış şeması kayıtlı. Altı grup koordinatörü 36'lık katalog içinde; Global Supervisor ayrıca bulunuyor. Sonraki altı rolün 12'lik aşaması tanımlı. Kaynaklarda ayrıntısı verilmeyen 24/36 aktivasyon sırasına kesinlik atfedilmedi.

### Zaman serisi ve veri kalitesi

Tek ölçüm yerine zaman penceresi kabul ediliyor. Eksik değerler, fiziksel aralık dışındaki ölçümler, tekrarlanan kimlikler, dönüş/üfleme sıcaklık tutarlılığı, zaman sırası, veri boşluğu ve güncellik ayrı denetleniyor. Eksik veri kaybolmuyor; fiziksel teşhis üretmeden açıklanabilir kalite raporuna dönüşüyor.

Sinyal analizi gerçek zaman farklarını kullanarak eğim, başlangıç/son bölüm farkı, varyans ve uygun olduğunda korelasyon hesaplıyor. Fan komutu, geri bildirim, hava debisi, soğutma gücü ve IT yükü ayrı değişkenler. Böylece yalnızca sıcaklık eşiği üzerinden neden iddia edilmesi önleniyor.

### Hipotez ve kanıt zinciri

B03 ölçülmüş belirtilere dayanan neden adayları üretiyor ve mevcut karşı kanıtları koruyor. Aynı belirtiyi üretebilen fan kaybı/geri bildirim sorunu belirsiz adaylar olarak gösteriliyor.

Her bulgu kaynak örneklere ve kanıt kimliklerine bağlı. F03 sayıları ham telemetriden yeniden hesaplıyor; kaynak, kimlik, iddia ve referans tutarlılığını kontrol ediyor. Son rapor da doğrulanmış bulgulardan türetilmiş haliyle karşılaştırılıyor. Böylece bir uzman çıktısının değiştirilmesi veya uydurma kanıt referansı nihai rapora sessizce taşınamıyor.

### Dinamik ve sınırlı yürütme

Normal akış 5, veri yetersizliği 3, anomali araştırması 6 rol çalıştırıyor. Gereksiz kök neden çalışması atlanıyor. Ajan, toplam araç, ajan başına araç ve süre bütçeleri eklendi. Yetkisiz araç, bozuk çıktı, başarısız doğrulama veya yürütme hatası nihai raporu engelliyor. Ajan görev kimlikleri, kullanılan araç sayısı, süre ve hata kodları kaydediliyor.

### Sentetik sistem

Tek bölgeli enerji dengesi ve basit fan kontrolü eklendi. Bir normal durum ve on arıza senaryosu üretilebiliyor: fan kaybı, sensör kayması, eksik sensör, yük artışı, soğutma kaybı, hava yolu kısıtlanması, fan geri bildirim uyumsuzluğu, iletişim kaybı, kontrol salınımı ve birleşik arıza.

Başlangıç saati ve tohum sabitlenerek tekrarlanabilir veri üretilebiliyor. Gerçek arıza etiketleri değerlendirme nesnesinde kalıyor; ajan girişinde senaryo adı veya arıza etiketi bulunmuyor. Bu ayrım ileride akademik deneyde cevabın sisteme sızmasını önlemek için gerekli.

### Tekrarlanabilir geliştirme

Kilitli bağımlılıklar, normal Python paket kurulumu ve ortak kalite kapısı hazırlandı. `scripts/check.py` kod denetimi, biçim kontrolü ve testleri sırayla çalıştırıyor; herhangi biri başarısızsa hata koduyla duruyor. Her sprintte aynı raporlama/test düzeninin izlenmesi `DEVELOPMENT.md` içinde kaydedildi.

## 3. Doğrulama sonuçları

Yerel ortam: macOS / ARM64 / Python 3.14.5.

- **113 pytest testi geçti.** Başarısız test yok.
- **Satır ve dal kapsamını birlikte değerlendiren toplam kapsam: %97,75.** Yapılandırılmış alt sınır %90.
- Ruff kod denetimi geçti.
- Ruff biçim kontrolü geçti.
- Normal durum ve on arızanın uçtan uca analizleri geçti.
- Her arıza başlamadan önceki normal bölümde yanlış alarm oluşmadığı kontrol edildi.
- Eksik/eski/gelecek tarihli veri, NaN/sonsuz, yanlış tür ve bilinmeyen alan kontrolleri geçti.
- Bozuk üretici kimliği, tekrarlı/değiştirilmiş kanıt, uydurma kanıt referansı, bastırılmış anomali, değiştirilmiş hipotez, doğrulayıcı sonucu ve son rapor testleri geçti.
- İzin, çağrı bütçesi, süre sınırı, hata sonrası durum izolasyonu ve hata metni gizleme testleri geçti.
- Enerji dengesi ve sinyal istatistikleri bağımsız hesaplanmış örneklerle doğrulandı.
- Kaynak dağıtımı ve wheel paketi üretildi.
- Wheel ayrı, boş bir Python ortamına çevrimdışı kuruldu; kaynak klasörünün dışından 11 senaryo, kurulu CLI ve geçersiz giriş çıkış kodu doğrulandı.

İlk test turunda elle hesaplanan bir test beklentisi yanlış yazılmıştı; beklenen eğim bağımsız hesapla düzeltilip testler yeniden geçirildi. Başlangıç kurulum denemesinde eksik kalite araçları indirildi; çalışma sırasında ağ servisi gerekmiyor.

Test kapsamı, teşhis doğruluğu veya hatasızlık garantisi değildir. Yazılım kontrolleri ile akademik başarım ölçümleri ayrı tutulmuştur. Python 3.12 ve 3.13 bu oturumda çalıştırılmadı; GitHub CI veya gerçek donanım testi yapılmadı.

## 4. Çalıştırma

Proje klasöründe:

```sh
.venv/bin/python scripts/check.py
.venv/bin/canovatwin --scenario fan_loss
.venv/bin/canovatwin --scenario sensor_missing
.venv/bin/canovatwin --scenario cooling_loss --format json --start 2026-10-28T00:00:00+00:00
```

Kaynaktaki değişikliklerden sonra kurulu CLI'yi güncellemek için README'deki yeniden kurulum komutunu kullanın.

## 5. Sınırlamalar ve sonraki kapsam

Sistem deterministik kurallarla çalışan bir çekirdektir. LLM, LangGraph, PostgreSQL, RAG ve web arayüzü henüz eklenmedi. Katalogda planlı görünen 30 rol uygulanmış değildir. Bunlar bu sprintin eksik testleri değil, sonraki aşamaların açık kapsamıdır.

Model parametreleri ve teşhis eşikleri örnektir. Fan arızalarının tümü birbirinden kesin olarak ayırt edilemez. Kanıt kontrolü fiziksel nedenin kesinliğini veya kodun bilimsel doğruluğunu kanıtlamaz. Açık HVAC/şirket verisiyle deney yapılmadı; F1 veya maliyet üstünlüğü iddiası yoktur.

Süre sınırı araçlardan önce/sonra denetlenir. Takılı kalan bir fonksiyonu zorla sonlandıran süreç izolasyonu yoktur; güvenilmeyen harici kod desteklenmez. Harici LLM/araç eklenmeden önce bu mekanizmalar ayrı kabul ölçütleriyle ele alınmalıdır.

Gerçek PLC bağlantısı ve fiziksel kontrol komutu bulunmuyor. Şubat 2027 entegrasyonu şirket erişimi ve uygunluğuna bağlıdır.

Sonraki sprint için doğal başlangıç, kalıcı olay/kanıt/çalışma kayıtları ve 12 rollük MVP'ye geçişin kabul ölçütleridir. Bu sprintin testleri geçmeden o kapsama geçilmemiştir.
