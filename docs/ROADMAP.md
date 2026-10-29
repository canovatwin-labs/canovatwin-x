# Ürün ve araştırma yol haritası

Bu belge özgün proje kapsamı ile çalışan 0.7.0 sürümü arasındaki farkı açık tutar.
Yerel Sprint 1–6'nın kapanmış olması, ilk önerideki bütün araştırma programının
veya 36 rolün tamamlandığı anlamına gelmez.

## Mevcut temel

12 deterministik uzman; katı veri sözleşmeleri; güvenli supervisor; sentetik
termal model; kanıtlı rapor; SQLite geçmiş ve replay; yerel API; React paneli.
Detay ve 36 rolün durumu: [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Öncelik 1 — Bağımsız değerlendirme

Gerekçe: Simülatörün arızayı belirli bir noktada başlatması ile analizdeki
ilk/son pencere karşılaştırması aynı tasarım varsayımlarına dayanır. Testlerin
geçmesi bağımsız arıza teşhis başarısını göstermemektedir.

- Sürüm, kaynak, lisans ve veri ayrımı kayıtlı deney manifesti.
- Değişken arıza başlangıcı, şiddeti, gürültüsü ve eksik veri oranları.
- Eğitim/ayar/değerlendirme ayrımı; etiketlerin ajan girdisine sızmaması.
- Precision/recall/F1, yanlış alarm ve Top-3 hipotez ölçümleri; süre ve aktif
  rol sayısı; model için MAE/RMSE; senaryo bazında hata analizi.
- İlk karşılaştırma: kural tabanı, core6 ve mvp12. Bunlar LLM karşılaştırması değildir.
- Kabul: aynı manifest tekrarlandığında aynı teknik sonuçlar; ayrı değerlendirme
  kümesi; başarısız örneklerin görünür olduğu rapor ve regresyon testleri.

## Öncelik 2 — Daha gerçekçi dijital ikiz ve telemetri

- Varlık/etiket kataloğu, birimler, örnekleme ve zaman kalitesi.
- Sürekli akış adaptörü, kayıt, yeniden bağlanma ve gecikme davranışları.
- Fiziksel varsayımları belgeli kalibrasyon; bağımsız ölçümle model doğrulama.
- Basamak/rampa/gecikme, bozucu etkiler ve kontrol tepkisi deneyleri.
- Kabul: kesinti ve sıra bozulması testleri; enerji/sıcaklık sınırları;
  fiziksel olarak açıklanabilir, tekrar üretilebilir deneyler.

Soğutma gücü elektrik tüketimi değildir. Toplam tesis ve IT elektrik gücü
olmadan PUE hesaplanmış gibi gösterilmez. Çoklu kabin ve CFD ayrı kapsamdır.

## Öncelik 3 — Operatör çalışma alanı

- Asset Explorer, Digital Twin Lab ve Experiment Lab iş akışları.
- Seçilen varlığa bağlı zaman serileri, deney karşılaştırması ve izlenebilir rapor dışa aktarma.
- Sürekli telemetri geldiğinde bağlantı durumu ve tazelik göstergeleri.
- Kabul: gerçekçi operatör görevleri, klavye erişimi, dar ekran, yüklenme/hata/boş
  durumlar ve uçtan uca kullanıcı akışları; yalnızca görsel kart eklemek yeterli değildir.

## Öncelik 4 — Bilgi erişimi ve uzman hiyerarşisi

- İzinli kaynaklarla belge alma, sürümleme, alıntı/kanıt bağları ve semantik arama.
- Değerlendirmesi yapılmış RAG; desteklenmeyen iddia oranı ve kaynak doğruluğu.
- Grup koordinatörleri, görev bağımlılıkları, checkpoint ve gerekçeli yönlendirme.
- İhtiyaç doğrulanırsa bütçeli LLM adaptörü; çevrimdışı deterministik temel korunur.
- 12 → 24 → 36 aktivasyon, her rolün sözleşmesi, aracı, hata yolu ve katkı ölçümüyle yapılır.

## Öncelik 5 — Sanal kontrolör ve saha hazırlığı

- Gerçek PLC olmadan test edilebilen kontrolör adaptör sözleşmeleri ve emülatör.
- Durum makinesi, haberleşme kesintisi, zaman aşımı ve güvenli hata davranışları.
- Saha öncesi protokol, erişim, veri izni ve yalnızca okuma entegrasyon planı.
- Şubat 2027 sonrası donanım erişimine bağlı saha doğrulaması. Fiziksel komut
  yürütme ayrı yetkilendirme, risk incelemesi ve kabul testleri gerektirir.

## Her aşamanın kapanış ölçütü

İş tanımı → küçük PR → ilgili testler → tüm kalite kapısı → diğer geliştiricinin
incelemesi → sonuç ve sınırlamalar raporu. Bulunan hatalar görünür iş olarak
izlenir; test geçmeden veya engel açıkça kaydedilmeden tamamlandı denmez.
