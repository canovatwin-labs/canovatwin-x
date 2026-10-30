# CanovaTwin X — Sprint 8 sonuç raporu

**30 Ekim 2026 · Uygulama 0.9.0 · Analiz motoru 0.4.0**

Bu sprint, bağımsız soğutma verisine geçişin ilk kod sınırını oluşturdu. Önceki
sentetik değerlendirme puanları gerçek veriye genellenmedi; indirilen ya da
şirkete ait veri depoya eklenmedi.

## Yapılanlar ve gerekçeleri

1. **Sürümlü kaynak manifesti:** Her veri kümesi kaynak URL'sini, lisans
   tanımlayıcısını ve inceleme notunu, CSV sütunlarını, fiziksel birimlerini,
   beklenen örnekleme aralığını ve train/validation/test parçalarını bildirir.
   Dosya SHA-256 değerleri, çalışma öncesi değişikliği yakalar. Kaynak ve lisans
   yalnızca beyan edilir; yazılım bunları doğrulanmış hak olarak göstermez.
2. **Birim ve zaman doğrulama:** °F/K→°C, kesir→%, m³/saat→m³/sn, W→kW
   dönüşümleri; eksik ve aralık dışı değer, medyan örnekleme süresi, en büyük
   boşluk ve gecikmiş örnek sayımı var. NaN, sonsuz, bozuk sayı/tarih, saat
   dilimsiz veya sıradan çıkan zaman damgası reddedilir. Eksik veri
   doldurulmaz, aralık dışı değer kırpılmaz.
3. **Deney ayrımı:** Aynı varlık farklı kümelerdeyse varsayılan varlık ayrımı
   bunu reddeder. Zaman ayrımı seçilirse aynı varlık için açık embargo gerekir.
   Farklı dosya adı, varlık veya zaman damgasıyla taşınmış aynı normalize ölçüm
   dizisi ayrıca yakalanır. Bu kontroller istatistiksel bağımsızlık kanıtı
   değildir.
4. **Sınırlı çevrimdışı CLI:** `canovatwin-dataset` bir manifestten CSV'leri
   okur ve yeni JSON raporuna yazar. Manifest 1 MB, dosya başına CSV 10 MB ve
   100.000 satır, toplam 100 parça ile sınırlıdır. Üst dizine ya da sembolik
   bağ ile dışarı çıkan yol reddedilir. Mevcut raporun üzerine yazılmaz.
5. **Dürüst sınır:** Rapor `declared_unverified` ve `not_connected` durumlarını
   taşır. Dış veri mevcut `synthetic` analiz sözleşmesine gizlice sokulmaz;
   gerçek tanı puanı veya saha doğruluğu üretilmez.

## Doğrulama

- **519 Python testi geçti**; 12 yeni test geçerli içe alma, hatalı birim/sütun,
  hash, sayısal değer, tarih/sıra, satır şekli, yol, split sızıntısı ve CLI
  üzerine yazmama davranışını denetledi. Ruff temiz, toplam satır+dal kapsamı
  **%97,25**. Bu yazılım kapsamıdır, teşhis doğruluğu değildir.
- **39 arayüz testi**, Prettier, TypeScript ve üretim derlemesi geçti. Sprint 8
  panel arayüzünü değiştirmedi. OpenAPI türleri yeni uygulama sürümüyle üretildi.
- Kaynak paketi ve wheel oluşturuldu; panel dosyaları ile MIT lisansı pakette
  doğrulandı. Boş ortamda kurulu 0.9.0 wheel ile üç parçalı **yerel test CSV'si**
  doğrulandı; rapor 3×3 satır, 60 sn medyan aralık, sıfır eksik ve sıfır aralık
  dışı değer verdi. Test CSV'si gerçek üçüncü taraf veri değildir.
- Aynı kurulu paketle gerçek yerel HTTP testi geçti: 22 referans + 33 dinamik
  birleşim, kimlik/yetki, geçmiş, replay ve dört eşzamanlı yazma. Önceki
  66 sentetik değerlendirme çalışması da geçti; teknik sonuç hash'i Sprint 7
  ile eşleşti. `actionlint` temiz.

## Katmanlar ve uzmanlar

L3/L4'e çevrimdışı kaynak doğrulama ve veri kalitesi özeti eklendi; endüstriyel
haberleşme veya sürekli akış eklenmedi. L1/L2/L5'in tek bölgeli sentetik modeli
ve L7'nin mevcut paneli korunuyor. L6'da Global Supervisor ve 12 deterministik
uzman çalışıyor; 36 katalog rolünün 24'ü planlı. Yeni içe alma aracı uzman rolü
değildir. LLM çağrısı ve fiziksel komut sıfır.

## Açık kalan işler ve sıradaki adım

Bir bağımsız HVAC/soğutma veri seti **henüz seçilmedi**. Sonraki adım kaynak
lisansı, sürümü, atıf şartları, sensörlerin fiziksel anlamı ve ölçüm birimlerini
yayıncı belgeleriyle doğrulamak; uygunsa manifesti gerçek dosyalarla doldurmak.
Ardından ayrı `open_dataset` kökenli, salt okunur bir analiz/değerlendirme
adaptörü ve ekipman/zaman ayrımlı hata analizi geliştirilmeli. Saha verisine
uygun olmayan alanlar için teşhis zorlanmamalı; eksik etiketler icat edilmemeli.

Gerçek PLC erişimi, şirket verisi, kalibrasyon, klasik ML/LLM kıyaslaması,
semantik RAG ve planlı 24 uzman hâlâ açık kapsamdır. Sprint 8 yazılım
kontrollerinin geçmesi bunların tamamlandığı anlamına gelmez.
