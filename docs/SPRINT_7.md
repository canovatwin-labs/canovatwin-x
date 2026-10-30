# Sprint 7 — Tekrar üretilebilir değerlendirme temeli

Amaç: çalışan çekirdeğin başarısını ölçülebilir hale getirmek; yeni ajan sayısı
iddiası üretmeden yöntemlerin aynı değerlendirme verisi üzerindeki farkını görmek.

## Kapsam ve kabul ölçütleri

1. Sürümlü ve katı deney manifesti; kaynak/lisans kaydı; ayrık train/validation/test
   seed grupları; yinelenen vaka ve veri sızıntısı reddi.
2. Mevcut dynamic-1.0 çıktısını değiştirmeden deneylerde arıza başlangıcı,
   şiddeti, sensör gürültüsü ve sensör-kayıp oranı ayarlama.
3. Aynı vakalarda bağımsız basit eşik tabanı, core6 ve mvp12 karşılaştırması.
   Etiketler/senaryo/seed/split hiçbir uzmana veya temel yöntem girdisine verilmez.
4. Alarm precision/recall/F1 ve yanlış alarm, etiket bazında aday F1 ve ilk üç
   aday kapsaması; tamamlanma/çekimserlik, süre p50/p95, çalışan rol sayısı;
   varsa model MAE/RMSE. Paydası olmayan metrik null olur.
5. Bloke çalışmalar sonuçlardan kaybolmaz; toplam/skorlanan/bloke sayıları ve
   hata satırları raporlanır. Başarısız ölçümler başarılı kabul edilmez.
6. Çevrimdışı CLI; JSON, CSV ve okunabilir Markdown raporu; çıktı üzerine yazmama;
   aynı girdilerde zaman ölçümleri dışında aynı sonuç özeti.
7. Elle hesaplanan metrik testleri, sızıntı ve hatalı manifest testleri, eski
   simülasyon regresyonları, CLI uçtan uca ve tam kalite/paket/HTTP kontrolleri.

## Sınırlar

Bu sentetik benchmark bir saha doğrulaması değildir. Veri yine proje içindeki
modelden gelir. Ayrı seed kümeleri gerçek veri veya bağımsız fizik modeli yerine
geçmez. LBNL/diğer açık veriler için lisans, alan farkı ve etiket eşlemesi ayrıca
çalışılacaktır. Train etiketi bu sprintte eğitim yapıldığı anlamına gelmez;
ayrılmış bir geliştirme kümesidir. Threshold ve yöntemler test sonucuna göre
otomatik ayarlanmaz. LLM, fiziksel komut, yeni uzman ve UI bu sprintte eklenmez.
