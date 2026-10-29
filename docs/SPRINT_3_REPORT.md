# Sprint 3 kapanış raporu — On iki uzmanlı çevrimdışı MVP

**Tarih:** 28 Ekim 2026  
**Sürüm:** 0.4.0  
**Sonuç:** A06/B05/B06/D02/D06/F02 entegre edildi; toplam 12 uygulanmış uzman, 36 kayıtlı rol.

## Yapılan işler ve gerekçeleri

### Eksik verinin ayrı araştırılması — A06

Eksik değerler sensör bazında sayılıyor; en uzun kayıp süre ve örnekleme boşlukları beklenen aralığa göre tahmin ediliyor. Eski akış ayrı işaretleniyor. Eksik değerler doldurulmadan, fiziksel teşhis üretilmeden kalite raporu hazırlanıyor. Bu, sensör sorunu ile gerçek ekipman arızasının karışmasını azaltan bir kontrol adımıdır.

### Geçmiş olay eşleme — B05

Önceki analizlerin belirti kodları deterministik Jaccard benzerliğiyle eşleniyor. Aynı ekipmandan, mevcut pencerenin başlangıcından önce bitmiş kayıtlar kullanılıyor; örtüşen/gelecek tarihli ve başka ekipmana ait kayıtlar dışlanıyor. En iyi üç eşleşme kaynak çalışma kimliğiyle raporlanıyor. Geçmiş hipotezler doğrulanmamış aday olarak kalıyor; yeni teşhis için gerçek arıza etiketi sayılmıyor.

### Kaynaklı yerel doküman arama — F02

Üç açıkça işaretlenmiş demo notu ve kullanıcı tarafından verilen JSON dokümanları üzerinde sözcük tabanlı, sınırlı parça araması eklendi. Alıntı; doküman kimliği, sürüm, içerik özeti ve karakter aralığıyla birlikte geliyor. Doküman metni talimat olarak çalıştırılmıyor. Bu sürüm vektör veritabanı veya LLM destekli RAG tamamlandı iddiasında değildir.

### Hipotez eleştirisi — B06

Adaylar destek ve karşı kanıtlarına göre korunmuş, zayıf veya belirsiz olarak ayrılıyor. Zayıf adaylar nihai hipotez listesinden ve what-if seçiminden çıkarılıyor; eleştiri kaydı raporda, ilk B03 çıktısı ise çalışma geçmişinde korunuyor. Böylece elemenin gerekçesi izlenebiliyor. Geçmiş/doküman bağlantıları bağlamdır; ölçüm kanıtının yerini almaz.

### What-if tasarımı — D02

Yükün başlangıç düzeyine dönmesi, soğutma kapasitesinin düzelmesi, fan takibi veya hava debisinin toparlanması için alternatif termal sonuçlar hesaplanıyor. Nominal soğutma kapasitesi sınırı aşılmıyor. Birden fazla hipotez aynı fan senaryosuyla sınanabilir. Sensör kayması ve kontrol parametresi hatası gibi bu basit modelle fiziksel karşılığı kurulmamış adaylar için sahte müdahale senaryosu üretilmiyor.

Bu hesaplar son pencere yükleriyle açık çevrim projeksiyonudur. Gerçek kontrolör komutu, fan parametresi yazımı veya nedensellik kanıtı değildir.

### Model doğrulama — D06

Referans sıcaklık ölçümleri ile modelin pencere boyunca tahmini karşılaştırılarak MAE/RMSE hesaplanıyor. Hata eşiği aşılırsa what-if değerlendirmeleri yalnızca açıklayıcı örnek olarak işaretleniyor. Bu test sentetik öz-tutarlılığı ölçer; gerçek tesis doğruluğu veya kalibrasyon değildir.

## Entegrasyon ve kayıt uyumluluğu

- Katalogdaki aktif rol sayısı 12; kalan 24 rol planlı.
- `core6` profili akademik karşılaştırma ve önceki akış için korundu.
- Yeni üretilen CLI senaryolarında varsayılan profil `mvp12`.
- JSON girişleri kendi araştırma profilini ve kaynaklarını taşır; dışarıdan sessizce değiştirilmez.
- Normal olayda 5, yetersiz veride 4, anormal olayda kaynaklara göre 9–11 rol çalışır. 12 rol aynı olayda zorla çalıştırılmaz.
- Araştırma kaynakları ve model ayarları girişte dondurulur. Tekrar çalıştırma güncel doküman veya veritabanına yeniden bakmaz.
- 0.3.0 motoruyla üretilmiş gerçek sentetik örnek kayıt okunup aynı içerikle yeniden saklanma testini geçti. Eski motor sürümünü yeni motor gibi çalıştırma guard'ı korundu; farklı motor sürümüyle replay reddedilir.
- Yeni altı çıktı, F03 kanıt doğrulamasına ve F04 raporuna dahil edildi. Değiştirilmiş sonuçlar nihai raporu engelliyor.

## Test sonuçları

Başlangıçta önceki 181 test geçti. Yeni profile özel ilk 36 test geçtikten sonra arşiv, snapshot, sayısal hesap ve CLI testleri tamamlandı. Son durumda:

- **242 pytest testi geçti; başarısız test yok.** Önceki sürüme göre 61 yeni kontrol eklendi.
- **Toplam satır+dal kapsamı %97,48.** Proje alt sınırı %90.
- Ruff kod denetimi ve biçim kontrolü geçti.
- On bir normal/arıza durumu yeni profille uçtan uca çalıştı.
- On iki rolün tamamı uygun senaryolarda çalıştırıldı; rol kaydı ile gerçek aktivasyon ayrı doğrulandı.
- Sahte doküman alıntısı, geçmiş eşleşmesi, hipotez eleştirisi, simülasyon ve hata metriği değişiklikleri raporu engelledi.
- Yetkisiz araç, sınırlı bütçe, yanlış kaynak özeti, yinelenen kaynak, büyük dosya ve doküman içindeki yönlendirici metin testleri geçti.
- MAE/RMSE ve enerji dengesi bağımsız elle hesaplanan örneklerle doğrulandı.
- Yanlış model parametresiyle modelin yetersiz olarak işaretlenmesi doğrulandı.
- Yeni geçmiş kayıtları ve sonradan değişen doküman dosyası, saklanmış analizin replay sonucunu değiştirmedi.

## Test sonuçlarının değerlendirmesi

İki profilde 11 senaryo, her biri üç kez çalıştırıldı: **66 sentetik analiz tamamlandı** ve tekrarlarda teknik raporlar aynı kaldı.

Normal, anomali ve veri yetersizliği sonuçlarında iki profil arasında durum farkı oluşmadı. Genişletilmiş profil altı anomali senaryosunda karşı kanıtla zayıflayan yük artışı adayını nihai listeden çıkardı. Fan performansı ile geri bildirim sorunu gibi ayırt edilemeyen adaylar belirsiz olarak korundu. Bu, yeni eleştiri adımının davranışını gösterir; tek başına teşhis doğruluğu üstünlüğü değildir.

Dokümanlı, geçmişsiz değerlendirmede `core6` 3/5/6, `mvp12` 4/5/10 rol çalıştırdı. Geçmiş eşlemenin dahil olduğu ayrı testlerde 11 rol çalıştı. Genişletilmiş profil ortalama daha fazla araç çağırdı; bu ek işin karşılığı kaynak bağlantıları, hipotez eleştirisi ve model denetimidir.

Varsayılan sentetik modelde anomali pencerelerinin referans sıcaklık hatası yaklaşık MAE=0.018516°C, RMSE=0.022628°C çıktı. Aynı model, seed ve parametreler kullanıldığı için bu düşük ve aynı hata değerleri beklenen öz-tutarlılıktır; gerçek dünyaya genellenemez. Kasıtlı parametre uyuşmazlığı testi bu yüzden ayrıca önemlidir: sistem yanlış modeli yeterli kabul etmedi.

Bu değerlendirme; Macro-F1, Top-3 accuracy, gerçek veri başarımı, LLM maliyeti veya istatistiksel olarak güçlü gecikme benchmark'ı değildir. Akademik karşılaştırma ve açık HVAC veri testleri henüz yapılmadı.

## Paket doğrulaması

0.4.0 wheel ve kaynak dağıtımı üretildi. Ayrı, temiz Python ortamına çevrimdışı kuruldu. Kaynak klasörü dışından 22 profil/senaryo birleşimi, geçmişli 11-rol akışı ve snapshot replay çalıştırıldı. Paket/motor sürümleri ve kurulu kaynakların çalışma kopyasıyla eşliği doğrulandı. Tüm 12 rol bu kontrollerde de çalıştı; LLM ve fiziksel komut sayısı sıfır kaldı.

Yerel ortam macOS / ARM64 / Python 3.14.5. Python 3.12/3.13, uzak CI, gerçek PLC, şirket verisi ve üretim ortamı bu oturumda test edilmedi.

## Kapanış ve kalan kapsam

Sprint 2 kaynak yedeği `work/canovatwin-sprint-2-backup.zip` içinde korunuyor. Çalışma yerel kaldı. Sprint 3'ün bilinen başarısız testi veya açık kabul ölçütü yoktur.

Ürünün tüm kapsamı tamamlanmış değildir: web/API, PostgreSQL, semantik RAG/LLM, gerçek PLC/gateway, grup koordinatörleri, diğer 24 rol ve akademik deneyler ileri kapsamdadır. Güncel katman ve rol durumu `PROJECT_STATUS.md` belgesinde ayrıntılı tutulur.
