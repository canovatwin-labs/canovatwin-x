# Figshare hastane AHU verisi: kaynak denetimi

Bu denetim, [Figshare v3 veri kaydındaki](https://doi.org/10.6084/m9.figshare.27147678.v3)
`hosptial_scientific_data.csv` dosyasını yayıncının MD5 değeriyle eşleştirir ve
[makaledeki](https://doi.org/10.1038/s41597-025-05825-9) tablo 5, 6 ve 8 ile
karşılaştırır. Veri kaydı **CC BY 4.0** lisansı bildirir; makalenin kendi lisansı
ayrıdır. Ham CSV depoya eklenmemiştir. Bu bir kaynak ve zaman kalitesi denetimidir;
ajanları çalıştırmaz, etiketleri model girdisi yapmaz ve teşhis puanı hesaplamaz.

## Tekrar üretme

Figshare v3 kaydından dosya adı değişmeden indirilmiş CSV'yi yerel bir dizine
yerleştirin. Araca ağ erişimi veya kullanıcı verisi gerekmez:

```sh
.venv/bin/canovatwin-hospital-audit /path/to/hosptial_scientific_data.csv --output audit.json
```

Komut 10 MB/100.000 satır sınırını, tam başlığı, yayıncı MD5 değerini, satır
biçimini ve saat başı zamanları doğrular. Mevcut çıktı dosyasını ezmez. JSON
raporunun bu kaynak dosyayla alınmış örneği:
[figshare_hospital_v3_audit.json](research/figshare_hospital_v3_audit.json).
Rapor ham ölçüm veya satır bazında etiket içermez. Dosyanın SHA-256 değeri
`66feab7fe66d77ca1c632315a61a7a93412ff00dc2fb0cd9b2485394cecca9f7`;
bu değer sonraki tekrar koşumlarında dosya eşitliğini gösterir.

## Gözlem ve yorum

- **66.048** satır ve altı etiketin tüm sayıları makalenin işlenmiş hastane
  verisi için verdiği tablo 6 ve 8 ile eşleşiyor.
- Makale toplama dönemini **2022** olarak bildiriyor. Yayıncı CSV'sindeki tüm
  66.048 kayıt **2023** tarihli; en erken 1 Ocak, en geç 21 Aralık. Yıl
  farklılığının nedeni bu veriden çıkarılamaz. Kaynağa soru sorulmadan
  tarih düzeltmesi yapılmamalı.
- Sekiz AHU'nun her biri 8.256 satır içeriyor; her birinde 23 yinelenen
  cihaz/saat anahtarı ve ilk-son saat aralığında 287 eksik saat var. Toplam
  yinelenen anahtar sayısı **184**. Dosya sıralı olmadığı için denetim zamanları
  cihaz başına küme olarak değerlendiriyor.
- Bazı sensör hücreleri boş: geri dönüş sıcaklığı 24, ısı eşanjörü ve ısıtma
  besleme sıcaklığı ayrı ayrı 28.416, soğutma besleme sıcaklığı ve pompa durumu
  ayrı ayrı 37.632. Bunlar otomatik doldurulmadı.

Makale etiketlerin uzmanlarca işletim aralıkları kullanılarak oluşturulduğunu,
örnek bir bölümün ayrıca kontrol edildiğini ve yayınlanan eğitim/doğrulama/test
bölmesinin rastgele katmanlı ayırma olduğunu açıklar. Aynı cihazın yakın saatleri
bu bölmelerde birlikte bulunabilir. Bu yüzden yayımlanan bölmeyi bağımsız saha
doğrulaması saymıyoruz. Ayrıca bir hastane AHU'su veri merkezi soğutma ünitesiyle
aynı fiziksel varlık değildir. Etiketlerin nedenlerinin ekipman üzerinden bağımsız
doğrulandığına dair bu araç kanıt üretmez. Şimdiki kullanım kaynak incelemesiyle
sınırlıdır; F1 veya saha teşhis başarısı iddiası yoktur.

Sonraki bilimsel adım, yayıncıdan yıl farkını açıklamasını istemek ve uygun
lisanslı bir kaynakta cihaz/zaman ayrımlı, önceden belirlenmiş değerlendirme
protokolünü incelemektir. Bunun öncesinde üretim kararları için bu etiketler
referans kabul edilmez.
