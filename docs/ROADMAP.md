# Ürün ve araştırma yol haritası

Bu belge özgün proje kapsamı ile çalışan 0.14.0 sürümü arasındaki farkı açık tutar.
Yerel Sprint 1–12'nin kapanmış olması, ilk önerideki bütün araştırma programının
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

Sprint 7 ile sürümlü sentetik manifest, ayrık seed kümeleri, değişken enjeksiyon,
üç yöntemin aynı ölçümlerde karşılaştırılması, açık paydalı metrikler ve
tekrar üretilebilir rapor çıktısı sağlandı. Bu madde **kısmen tamamlandı**:
bağımsız açık/saha veri kümesi, ekipman ve zaman ayrımlı dış doğrulama, belirsizlik
aralıkları ve daha geniş örneklem henüz yok. Sentetik sonuçlar saha başarısı
iddiasına dönüşmez.

Sprint 8 dış CSV verisi için kaynak/lisans beyanı, birim eşleme, dosya hash'i,
zaman kalitesi ve varlık/zaman ayrımlı split doğrulamasını ekledi. Gerçek açık
veri seti henüz seçilip lisans ve semantik incelemesinden geçirilmedi; dış veri
üzerinde tanı puanı iddiası yok.

Sprint 9 doğrulanmış CSV penceresini `declared_external` kökeniyle yalnızca
keşif amaçlı altı uzmanlı incelemeye bağladı. Etiketler bilinmiyor ve insan
incelemesi zorunlu. Bu teknik yolun bulunması, bağımsız veri seti doğrulaması
veya başarı ölçümü anlamına gelmez.

Sprint 12, AAU Zenodo v5 sunucu odası kaydındaki iki küçük gerçek ölçüm CSV'sini
lisans/sürüm/hash beyanıyla doğruladı ve zaman ayrımlı keşif incelemesine soktu.
İki kanal ve etiketsiz veri nedeniyle çekimser sonuç çıktı; gerçek veri üzerinde
bir uçtan uca kalite yolu var, fakat arıza tanı başarısı hâlâ ölçülemedi.

Sprint 13 için Figshare v3 hastane AHU dosyası salt okunur kaynak denetimine
alındı. Dosya ile makalenin satır ve etiket sayıları eşleşiyor; bildirilen
toplama yılı uyuşmuyor ve yinelenen cihaz/saat anahtarları var. Ayrıntı:
[FIGSHARE_HOSPITAL_AUDIT.md](FIGSHARE_HOSPITAL_AUDIT.md). Bu çalışma veri merkezi
arıza teşhis başarısı üretmez; bağımsız değerlendirme hâlâ açık.

## Öncelik 2 — Daha gerçekçi dijital ikiz ve telemetri

- Varlık/etiket kataloğu, birimler, örnekleme ve zaman kalitesi.
- Sürekli akış adaptörü, kayıt, yeniden bağlanma ve gecikme davranışları.
- Fiziksel varsayımları belgeli kalibrasyon; bağımsız ölçümle model doğrulama.
- Basamak/rampa/gecikme, bozucu etkiler ve kontrol tepkisi deneyleri.
- Kabul: kesinti ve sıra bozulması testleri; enerji/sıcaklık sınırları;
  fiziksel olarak açıklanabilir, tekrar üretilebilir deneyler.

Sprint 10, taşıma protokolünden bağımsız çevrimdışı akış sözleşmesiyle geliş
ve ölçüm zamanını ayırdı; sıra bozulması, geç veri, tampon dolması ve bağlantı
durumunu sınadı. Kalıcı kayıt, yeniden başlatma sonrası devam, gerçek ağ geçidi
ve fiziksel model kalibrasyonu hâlâ açık.

Sprint 11 atomik SQLite olay günlüğüyle yeniden başlatma sonrası akış durumunu
kurdu; bozulma ve eşzamanlı yazar durumlarını test etti. Gerçek ağ geçidi,
uzun süreli arşiv/rotasyon ve fiziksel kalibrasyon hâlâ açık.

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
