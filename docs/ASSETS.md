# Varlık kataloğu ve ekipman çalışma alanı

Katalog, **yapılandırılmış sentetik üniteleri** ve **yalnızca geçmişte gözlenen
kimlikleri** birlikte listeler. İkinci grup için konum veya fiziksel model
uydurulmaz. Olay, açık/incelemede olay ve çalışma sayıları seçilen ekipmanın
tüm kalıcı kayıtlarından hesaplanır. Son çalışma, kayıt sırasına göre belirlenir;
bu zaman bir canlı cihaz bağlantısının göstergesi değildir.

## Yerel yapılandırma

API yapılandırmasının isteğe bağlı `assets` alanı, başlangıçta doğrulanan
1–100 tanım içerir. Yapılandırma dosyasının mevcut 16 KB sınırı da geçerlidir.
Varsayılanlar iki sentetik ünitedir. Her ikisi aynı tek bölgeli 10 kW modelin
bağımsız koşumudur; ikinci ünitenin önerilen yükü 6 kW / `batch`, birincininki
4,2 kW / `cyclic` olarak tanımlıdır. Aralarında ısıl etkileşim modellenmez.

Mevcut anahtarları değiştirmeden yalnızca `assets` alanı eklenebilir:

```json
{
  "assets": [
    {"asset_id":"synthetic-unit-01","name":"Pilot ünite","location":"Sentetik alan","default_conditions":{"workload":"cyclic","baseline_load_kw":4.2,"ambient_c":30,"fan_response_s":6}}
  ]
}
```

Bu örnek tek başına tam API yapılandırması değildir; mevcut `database`,
`read_token` ve `write_token` korunmalıdır. Tanım değişiklikleri sunucu yeniden
başlatılınca yüklenir. Kimlikler benzersiz ve URL güvenli olmalıdır; eski
istemciler için `synthetic-unit-01` tanımı zorunludur. Kaynak yalnızca
`synthetic` olabilir; URL, PLC adresi veya kontrol komutu kabul edilmez.
Tanımlar panelden değiştirilemez; kişisel kullanıcı/izin sistemi veya
konfigürasyon değişikliği denetim geçmişi bu sürüme dahil değildir.

Tanımdan çıkarılan bir ekipmanın geçmişi silinmez: katalogda gözlenen kimlik
olarak kalır. Bu kimlikle yeni hazır senaryo/aktarım deneyi açılmaz. İsim ve
konum güncel katalog metadatasıdır; geçmiş ekipman adı snapshot'ı değildir.
Kaydedilen üretim koşulları ve analiz girdileri ise değişmez.

## HTTP ve panel

- `GET /api/v1/assets?limit=10&offset=0`: yapılandırılmış ve gözlenen kimlikler;
  benzersiz kimliğe göre sıralı, sınırlı sayfa.
- `GET /api/v1/assets?configured_only=true&limit=100`: deney seçicisinin tüm
  yapılandırılmış hedefleri; gözlenen kimlikler bunları sayfadan dışlayamaz.
- `GET /api/v1/assets/detail?asset_id=...`: tanım, sayaç ve 11 kanonik sensör
  etiketi, birimi ve örnek kalite aralığı. Özel karakterli eski kimlikler için
  sorgu değeri URL kodlanır; SQL değerleri parametre olarak bağlanır.
- `GET /api/v1/incidents?asset_id=...`: aynı ekipmana ait sayfalanmış olaylar;
  isteğe bağlı mevcut `status` filtresiyle birlikte çalışır.

Okuma anahtarı bu yolları kullanabilir. Hazır senaryo ve aktarım API'leri yazma
anahtarı ve yapılandırılmış `asset_id` ister; alan atlanırsa eski varsayılan
korunur. Dinamik koşullar ekipman varsayılanlarının üzerine açık alanlarla
uygulanır. Referans model seçildiğinde eski sabit üreticinin davranışı korunur.
Genel `/analyses` yolu eski ad hoc sentetik pencereleri kabul etmeye devam eder;
bu yoldaki yeni kimlik kataloğa otomatik fiziksel tanım eklemez.

Panelde **Ekipmanlar → ekipman → analiz/aktarım → rapor → ekipman** akışı vardır.
Seçilen ekipmanın son kayıtlı penceresi, zaman grafiği, son değerleri, pencere
başına eksik ölçüm sayısı ve olayları gösterilir. Son değer eksikse önceki
değerle doldurulmaz. Üretici emniyet sınırı veya PUE iddiası yapılmaz.

## Uyumluluk

SQLite şeması değiştirilmedi. Eski ayarlar varsayılan katalogla açılır; eski
üretim metadatasında olmayan ekipman kimliği varsayılan kimlikle yüklenir.
`transport-1.0` parmak izi, eski varsayılan ekipman anahtarını normalleştirerek
korunur. Yeni ekipmanın üretim metadatası, penceresi ve akış yapılandırması aynı
kimliği taşımak zorundadır. Ajanlar katalog adını veya arıza senaryosunu girdi
olarak almaz; analiz motoru 0.4.0 korunur. Geçmiş vaka sorgusu sayfalanmadan önce
ekipmana göre süzülür; başka ekipman kayıtları ilgili eski vakaları dışlayamaz.
