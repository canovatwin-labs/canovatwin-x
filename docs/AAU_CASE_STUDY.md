# AAU sunucu odası açık veri vaka çalışması

**Kaynak:** [Aalborg University Zenodo kaydı, sürüm v5](https://zenodo.org/records/21262042),
DOI [10.5281/zenodo.21262042](https://doi.org/10.5281/zenodo.21262042).
Yayıncı kaydının makine okunur metadatası lisansı **CC BY 4.0** olarak bildirir.
Atıf ve lisans koşulları korunmalıdır. Ham veri bu depoda yer almaz.

## Tekrar üretme

Zenodo v5 kaydından değiştirilmemiş
`AAU_supplementary_ventilation.csv` ve
`AAU_supplementary_surrounding_temperatures.csv` dosyalarını aynı yerel klasöre
indirin. Ardından yeni bir çıktı klasörü seçin:

```sh
.venv/bin/canovatwin-aau /path/to/zenodo-files --source-offset +02:00 --output-dir .local/aau-v5
```

`+02:00`, kaynak CSV zamanlarının Eylül–Ekim 2024 aralığı için **açıkça
bildirilen bir yorumdur**; yayıncı dosyalarında saat dilimi yazmadığı için
doğrulanmış saat dilimi diye sunulmaz. Farklı bir yorum gerekiyorsa adaptör
yeniden çalıştırılıp sonuçlar ayrı tutulmalıdır. CLI ağdan dosya indirmez.

Adaptör yayıncının iki MD5 değerini kontrol eder, ayrıca ham dosyaların SHA-256
değerlerini rapora yazar. Yalnızca zaman damgası birebir eşleşen ve gerçekten
ölçülmüş `AHU_temperature_supply` ile `Outdoor_temperature` çiftlerini alır.
Bu alanlar °C yorumu ile sırasıyla `supply_c` ve `ambient_c` olarak eşlenir; diğer dokuz
kanal uydurulmaz. Farklı zamanlardaki ölçümler doldurulmaz veya yakın komşuyla
eşleştirilmez. Çıktı `manifest.json`, üç CSV ve `report.json` içerir;
var olan çıktı klasörü üzerine yazılmaz.

## 31 Ekim 2026 yerel koşumunun gözlemleri

- Kaynak dosyalar SHA-256: ventilation
  `72de6d7ca9d0530030cf42b775bbe812a9ed8e57b0e2eee2dff0f1f7a8869c54`,
  surroundings
  `a8010675dce89f2dba11615caf76b8a24648a52ac38f7226a461d4c59348f26e`.
- **1.521** birebir zaman eşleşmesi; iki zaman ayrımı için **10** ölçüm
  dışarıda bırakıldı. Train **503**, validation **503**, test **505** satır.
- Medyan örnekleme aralığı her kümede **900 saniye**. Train ve validation
  kümelerinde birer boşluk sayıldı; testte yok. Eşlenen iki kanalda eksik ve
  aralık dışı değer sayısı sıfır.
- Test penceresinde analiz `insufficient_data` ve
  `human_review_required=true` döndü. Arıza etiketi bilinmiyor.

Bu sonuç, gerçek sunucu odası ölçümlerinin veri kalitesi ve köken sınırından
geçebildiğini gösterir. İki sıcaklık kanalı fan, debi, IT yükü, soğutma gücü ve
sensör karşılaştırması için yeterli değildir. **F1, teşhis doğruluğu veya
kalibrasyon başarısı çıkarılamaz.** Yayıncı MD5 kontrolü ve beyan edilen lisans,
bağımsız hukuki hak doğrulamasının veya saha sensör kalibrasyonunun yerini almaz.
Sıcaklık birimi ve sensör konumu da teşhis eşikleriyle karşılaştırılmadan önce
yayıncının ölçüm dokümantasyonuyla ayrıca teyit edilmelidir.
