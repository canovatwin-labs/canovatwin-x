# CanovaTwin X — Sprint 7 sonuç raporu

**30 Ekim 2026 · Uygulama 0.8.0 · Analiz motoru 0.4.0**

Bu sprint, mevcut teşhis akışını ölçülebilir ve yeniden çalıştırılabilir bir
deneye dönüştürdü. Yeni uzman eklenmedi; 36 kayıtlı rolden 12'si çalışıyor.
Raporun sonuçları yalnızca proje içindeki sentetik üretici için geçerlidir.

## Yapılanlar ve nedenleri

1. **Ayrık deney manifesti.** Kaynak/lisans, üretici sürümü, senaryo, koşullar,
   tohum ve `train`/`validation`/`test` ayrımı kayda giriyor. Aynı tohumun farklı
   kümelerde kullanılması, yinelenen yapılandırma ve kimlik/zaman değiştirilerek
   kopyalanan aynı telemetri reddediliyor. Böylece yanlışlıkla veri sızıntısı ve
   tekrarlanamayan deney riski azalıyor. Ayrı tohum, bağımsız fizik modeli veya
   saha verisi anlamına gelmiyor.
2. **Değerlendirmeye özel enjeksiyonlar.** Arızanın başladığı nokta, şiddeti,
   sensör gürültüsü ve eksik örnek oranı değiştirilebiliyor. Mevcut `dynamic-1.0`
   algoritması değiştirilmedi; 33 tarihsel senaryo/profil ölçüm serisi 0,001
   birim duyarlıkta sabit tutuluyor.
3. **Üç yöntem, aynı ölçümler.** Ajan kullanmayan basit eşik yöntemi, `core6` ve
   `mvp12` aynı telemetriyi alıyor. Gerçek etiket, seed, split ve enjeksiyon
   ayarları tahmin sınırının dışında kalıyor. `mvp12` yalnızca sabit yerel demo
   notlarını kullanıyor; deney vakaları geçmiş eşleme kaynağına dönüşmüyor.
4. **Açık paydalı rapor.** Alarm precision/recall/F1, yanlış alarm, etiket
   bazında aday puanları, macro-F1, ilk üç aday kapsaması, bloke çalışma oranı,
   süre, aktif rol ve model hata ölçüleri JSON, CSV ve Markdown olarak çıkıyor.
   Paydası olmayan oran `null`/`n/a`; bloke çalışma skor dışında açıkça sayılıyor.
   Var olan çıktı klasörünün üzerine yazılmıyor.
5. **Dağıtım yolu.** Yeni `canovatwin-evaluate` komutu wheel'den kurulu ortamda
   çalışıyor. CI, Python 3.12/3.13/3.14 üzerinde paketi kurup bu örnek deneyi
   çalıştıracak şekilde genişletildi. Birleşen `jsdom` 30 sürümünün Node alt
   sınırı geliştirme belgelerinde ve paket koşulunda düzeltildi.

## Testler ve sonuçları

- Yerelde **507 Python testi** geçti; Ruff denetimi/biçimi temiz, satır+dal
  kapsamı **%98,00**. Önceki 437 testten 70 test eklendi. Elle hesaplanan metrik,
  hatalı/sızdıran manifest, bloke çalışma, CLI, 33 tarihsel üretici serisi ve
  tüm senaryo/yöntem birleşimleri test edildi.
- **39 arayüz testi** geçti; Prettier, TypeScript ve üretim derlemesi temiz.
  Yeni bir arayüz akışı eklenmedi. OpenAPI'den üretilen tipler değişmeden kaldı.
- Kaynak dağıtımı ve wheel oluşturuldu. Wheel içindeki panel dosyaları kaynakla
  birebir eşleşti; MIT lisans metadatası ve dosyası doğrulandı. Paket boş bir
  ortama kuruldu. Kurulu paketle gerçek loopback HTTP testi geçti: 22 referans +
  33 dinamik birleşim, yetki, kayıt, durum, replay ve dört eşzamanlı yazma.
- Örnek manifestte **66 vaka** var; test kümesindeki 22 vaka üç yöntemle toplam
  **66 çalışma** üretti. Bloke çalışma yok. Aynı ortamda iki bağımsız koşunun
  `result_sha256` değeri eşleşti; kurulu wheel de aynı teknik sonuç hash'ini
  verdi. Süreler hash dışında tutulur ve koşudan koşuya değişir.
- `actionlint` temiz; temiz `npm ci` sonrasında npm denetimi **0 güvenlik
  bulgusu** bildirdi. Linux GitHub CI sonuçları PR incelemesinde ayrıca
  doğrulanmalıdır; yerel test onların yerine geçmez.

İlk Linux CI koşusu ham JSON hash'li 11 tarihsel vakada başarısız oldu: macOS
ve Linux matematik kütüphaneleri sinüs hesaplarının son bitlerinde ayrılıyor.
Üretici kodunu değiştirmeden regresyonu tüm seri için 0,001 birimlik kanonik
karşılaştırmaya çevirdik. Düzeltmenin Linux CI sonucu PR üzerinde ayrıca
doğrulanacak.

## Sentetik test kümesinin okunması

| Yöntem | Alarm F1 | Aday macro-F1 | İlk üçte gerçek etiket payı | Bloke |
| --- | ---: | ---: | ---: | ---: |
| Basit eşik | 0,824 | 0,715 | 0,675 | 0/22 |
| core6 | 1,000 | 0,601 | 0,750 | 0/22 |
| mvp12 | 1,000 | 0,649 | 0,750 | 0/22 |

Alarm sonuçları bütün yöntemlerde aynı 22 vakanın yalnızca **iki normal**
örneğini içeriyor. Bu nedenle gözlenen sıfır yanlış alarm oranı güçlü bir saha
güvencesi değildir. `core6` ve `mvp12` alarmı iyi yakalasa da aday macro-F1
değerleri daha düşük; bazı etiketleri hiç bulmuyor ve bazılarını fazla öneriyor.
`insufficient_data` dört vakada güvenli çekimserliktir, kök neden başarısı
değildir. `mvp12` için 16 model vakasında ortalama MAE/RMSE sıfır çıkması,
modelin kendi üreticisiyle tutarlılığıdır; bağımsız termal doğrulama değildir.
Yerel p50/p95 süreleri bir makine gözlemidir, performans garantisi değildir.

Ham sonuçlar sürüm kontrolü dışındaki `work/sprint7-evaluation-a/` klasöründe
saklandı. Yeniden üretme komutu ve paydaların tanımı [değerlendirme
protokolünde](EVALUATION.md) bulunur.

## Katman ve uzman durumu

- **L1/L2/L5:** Tek bölgeli sanal tesis, gecikmeli ekipman/kontrol davranışı,
  değişken sentetik enjeksiyon ve sınırlı what-if/model ölçümü çalışıyor. Saha
  kalibrasyonu, çoklu bölge ve gerçek kontrolör yok.
- **L3/L4:** Pydantic/JSON ve yerel API sınırı, SQLite inceleme geçmişi, audit
  ve replay çalışıyor. Endüstriyel protokol ve kurumsal veri altyapısı yok.
- **L6:** Global Supervisor ve **12 deterministik uzman** aktif; 36 kayıtlı
  rolün 24'ü planlı. Yeni değerlendirme modülü uzman değildir. LLM çağrısı ve
  fiziksel komut sıfır.
- **L7:** CLI, API ve mevcut React paneli çalışıyor. Değerlendirme raporu CLI
  üzerinden alınır; panelde deney karşılaştırma ekranı henüz yok.

Aktif uzmanlar: **A02, A03, A06; B02, B03, B05, B06; D02, D06; F02, F03,
F04.** Roller ve sınırları [güncel durum belgesinde](PROJECT_STATUS.md) tek tek
listelenmiştir.

## Açık kalan işler ve sıradaki adım

Öncelik 1'in sentetik ölçüm temeli hazır. Sıradaki iş, lisansı ve kaynak geçmişi
uygun bir **bağımsız açık HVAC/soğutma veri kümesini** envantere almak; birim,
örnekleme, ekipman ve etiket eşlemesini belgelemek; veri sızıntısını ekipman ve
zaman ayrımıyla önlemek. Uygun veri bulunursa mevcut değerlendirme sözleşmesine
uyarlama, güven aralıkları ve hata analizi yapılmalı. Bulunamazsa sentetik puanlar
bağımsız başarı olarak sunulmamalı. Sonraki sırada daha gerçekçi varlık/etiket
kataloğu, akış/bağlantı davranışı ve operatör deney karşılaştırma ekranı var.

Gerçek şirket verisi, gerçek PLC erişimi, eğitimli ML/LLM karşılaştırması,
semantik RAG, 24 planlı uzman ve saha validasyonu bu sprintte tamamlanmadı.
