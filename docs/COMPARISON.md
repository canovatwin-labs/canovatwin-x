# Kayıtlı koşum karşılaştırması

`comparison-1.0`, aynı ekipmana ait iki farklı kayıt üzerinde salt okunur,
betimleyici karşılaştırma üretir. Analiz motorunu yeniden çalıştırmaz, LLM veya
fiziksel komut kullanmaz. Veritabanı şeması ve analiz motoru 0.4.0 değişmez.

## Kullanım

Okuma veya yazma yetkili bearer anahtarıyla:

`GET /api/v1/comparisons?baseline=RUN-...&candidate=RUN-...`

Kimlikler mevcut çalışma ayrıntısından veya olayın `/runs` listesinden alınır.
Bu sürüm karşılaştırma API'sini sağlar; panelden seçim ve yan yana gösterim
sonraki ayrı geliştirmedir. Anahtar URL'ye konmaz.

- Tam olarak iki kayıt okunur; kimlikler 1–100 URL güvenli karakterle sınırlıdır.
- Kayıt bulunamazsa 404; aynı kayıt veya farklı ekipman seçilirse
  409 `COMPARISON_INCOMPATIBLE`; geçersiz sorgu 422; anahtarsız istek 401.
- Sayısal fark sonlu float sınırını aşarsa 409 döner; sonsuz veya sahte sıfır dönmez.
- Farklı motor, kaynak, profil, işletim koşulu veya zaman aralığı karşılaştırılabilir;
  bunların eşdeğer deney olduğu iddia edilmez. Engellenmiş analiz de gerçek durumuyla görünür.

## Yanıtın anlamı

`baseline` ve `candidate` kayıt/olay kimliğini, kayıt zamanını, motoru, kaynağı,
gözlenen pencerenin başlangıç/bitişini, örnek sayısını, analiz/rapor durumunu ve
varsa aktarım sayaçlarını verir. Kaydedilmiş üretim bilgisi olmayan referans ve
özel girdiler `reference_or_custom` olarak işaretlenir; üretim reçetesi tahmin edilmez.
Aktarım deneyi olmayan kayıtta aktarım sayıları `null` olur; kayıp yokmuş gibi sıfır gösterilmez.

On bir kanonik kanal için iki tarafta geçerli/eksik okuma sayısı, minimum,
maksimum, aritmetik ortalama ve en son ölçüm zamanındaki değer bulunur.
Tüm sonlu mevcut okumalar dahildir; kalite aralığı dışındaki okumalar otomatik
silinmez. Tanı raporu ayrıca okunmalıdır. Aritmetik ortalama zaman ağırlıklı
değildir; yeniden örnekleme, boşluk doldurma veya aykırı değer temizleme yapılmaz.
Son okuma eksikse `final` ve `final_delta` `null` kalır. Tamamen eksik kanalda
bütün istatistikler ve farklar `null` olur. Fark yönü her zaman **aday − temel**dir.

`differing_inputs`, motor, kaynak, saat, politika, araştırma snapshot'ı, mevcut
üretim reçetesi, aktarım profili ve örnek sayısındaki değişen alanların yollarını
verir. `telemetry_sha256` serileştirilmiş pencere farkını işaretler. Belge içeriği,
anahtar veya aktör bilgisi bu özetin içine kopyalanmaz. Ayrıntı için değişmez asıl
koşum kaydı kullanılır. `same_measurement_timestamps` tüm ölçüm zamanlarının
aynı sırada eşit olduğunu söyler; karşılaştırma bir noktasal hizalama yapmaz.

Sonuç bir iyileşme sıralaması, nedensellik veya tanı başarısı ölçümü değildir.
Eşit olmayan süreler ve eksik veri dağılımı farkları yanıltabilir. Termal soğutma
gücü elektrik tüketimi değildir; enerji integrali, tasarruf veya PUE hesaplanmaz.
Bağımsız etiketli doğrulama ve fiziksel kalibrasyon gereksinimleri sürer.

## İzlenebilirlik

Aynı iki değişmez kayıt aynı yanıtı üretir; sunum zamanı veya rastgele kimlik
üretilmez. Replay kaydı ayrı kimliğiyle seçilebilir. Karşılaştırma yeni koşum,
olay revizyonu veya audit olayı oluşturmaz. Saklanan kayıtları değiştirmez.
