# Sprint 13 sonuç raporu — yayıncı veri denetimi

**31 Ekim 2026 · Bağımsız geliştirme dalı**

## Ne yapıldı, neden?

Figshare v3 hastane AHU dosyası için salt okunur, çevrimdışı bir denetim komutu
ve Pydantic rapor sözleşmesi eklendi. Amaç, açık veri bulunmasını bağımsız teşhis
doğrulamasıyla karıştırmamak ve kaynak/versiyon sorununu deneyden önce yakalamak.
Dosya adı, yayıncı MD5'i, SHA-256, şema, cihaz/saat anahtarları, boş hücreler,
etiketler ve makaledeki üç tablo açıkça karşılaştırılıyor. Denetim ham dosyayı
depoya yazmıyor, bir ölçümü değiştirmiyor ve mevcut çıktıyı ezmiyor.

## Gerçek kaynak koşumu

66.048 satır ve etiket sayıları makaleyle eşleşti. Tüm CSV tarihleri 2023 iken
makale 2022 bildiriyor. Sekiz AHU'da toplam 184 yinelenen cihaz/saat anahtarı
ve her cihazın gözlem aralığında 287 eksik saat saptandı. Beş sensör sütununda
boş hücreler var. Kaynak ve lisans, bulgular ve sınırlar
[vaka notunda](FIGSHARE_HOSPITAL_AUDIT.md) ve
[makine okunur raporda](research/figshare_hospital_v3_audit.json) kayıtlıdır.

## Test ve kabul

Sentetik testler zaman/etiket/eksik veri özetini, yayıncı checksum reddini,
değişen başlık ve satır biçimini, saat dışı zamanları, sembolik bağlantıyı ve
mevcut çıktı dosyasını korumayı sınar. Tam Python ve panel kalite kapısı ayrıca
çalıştırıldı: **530 Python testi**, **39 panel testi** geçti; Python toplam
satır+dal kapsamı **%96,66**. Ruff, Prettier, TypeScript ve panel üretim derlemesi
temiz. Kilit dosyası çevrimdışı doğrulandı; kaynak ve wheel paketleri oluşturuldu.
Wheel içinde yeni komut giriş noktası, panel ve MIT lisansı doğrulandı. Aynı
yayıncı dosyasıyla denetim tekrar çalıştırılıp sürümlü JSON rapor üretildi.
GitHub CI sonucu PR'da ayrıca doğrulanacaktır.

Bu sprint **teşhis doğruluğu üretmez**. 12 uzman, akış, günlük ve gerçek PLC
bu dalın kapsamı dışındadır. Yayıncıdan yıl farkı açıklaması alınmadan veya
bağımsız cihaz/zaman ayrımı kurulmaksızın dış performans iddiası yapılmaz.
