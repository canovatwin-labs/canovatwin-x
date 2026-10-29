# Sprint 5 sonuç raporu — Yerel inceleme paneli

**28 Ekim 2026 · Uygulama 0.6.0 · Analiz motoru 0.4.0**

## Hedef ve yapılanlar

CLI/API ile çalışan çekirdeğe, gerçek API kullanan Türkçe bir operatör paneli eklendi. React/TypeScript kaynağı `web/` altında; derleme Python paketinde taşınıyor. Aynı servis `/panel/` üzerinden ekranları açıyor. Günlük kullanım için ayrı Node sunucusu veya internet bağlantısı gerekmiyor.

Tamamlanan akışlar:

1. Yerel anahtarla bağlanma, sunucudan okuma/yazma rolünü öğrenme, çıkış ve yenilemede bellekteki oturumu temizleme.
2. Olay listesi, durum filtresi ve onarlı sayfalama. Görünen sayfa sayısı toplam kayıt sayısı olarak sunulmuyor.
3. On bir sentetik senaryo, iki uzman profili, örnek sayısı ve tohum seçerek analiz başlatma; kaydedilen çalışmanın ayrıntısına gitme.
4. Rapor, gözlem, neden adayı/karşı kanıt, eleştiri, dondurulmuş doküman alıntıları, geçmiş eşleşmeleri, model hataları ve what-if sonuçlarını inceleme.
5. Sıcaklık grafiği ve tüm sensör alanlarının tablosu. Eksik değerleri boş bırakma; zaman boşluklarında çizgiyi kesme.
6. Kanıt kimliği, kaynak ölçümleri ve ajan çıktılarını izleme. Tamamlanan adım ile başarısız aktivasyon girişimi ayrı sayılıyor.
7. Gerekçeli, revizyon kontrollü inceleme durumu değişikliği; kayıtlı girdilerle yeniden analiz, eşleşme/fark gösterimi ve denetim geçmişi.
8. Katalogda 36 rolün uygulanmış/planlı durumunu görme. Yeni uzman eklenmedi; çalışır rol sayısı 12 olarak kaldı.

## Neden bu şekilde yapıldı?

- **Tek servis:** Kullanıcının Mac üzerinde iki uygulama çalıştırması gerekmiyor. CORS, ayrı dağıtım ve çalışma zamanı CDN bağımlılığı eklenmiyor.
- **Katı sözleşme:** TypeScript türleri FastAPI OpenAPI şemasından üretiliyor. Şema gerçek API ile test ediliyor; eski ve yeni veri şekilleri rastgele tahmin edilmiyor.
- **Bellek içi anahtar:** Anahtar URL, tarayıcı depoları veya loglara yazılmıyor. Çıkış bekleyen istekleri iptal ediyor; geç yanıt eski oturumu canlandıramıyor. Yetki her istekte API tarafından da kontrol ediliyor.
- **Sonuç ayrımı:** HTTP201, `completed`, `blocked` ve rapor kararı aynı şey değildir. Engellenmiş çalışmada nihai rapor gösterilmiyor. Yeniden analizde `matches=false` görünür bir inceleme sonucudur.
- **Kontrollü yazma:** Çift gönderim engelleniyor; POST isteği otomatik tekrar edilmiyor. Bağlantı koparsa önce geçmişi kontrol etme yönlendirmesi var. Revizyon çakışmasında yeni durum yükleniyor ve yazılan gerekçe korunuyor.
- **Ölçümün anlamı:** Eksik sıcaklık sıfıra çevrilmiyor. Zaman ekseni örnek indisinden değil gerçek zaman farkından hesaplanıyor. Küçük ekranda grafik yazıları küçültülmeden koordinat alanı yeniden hesaplanıyor.
- **Sürüm ayrımı:** Kullanıcı erişimi değiştiği için uygulama 0.6.0; analiz algoritması değişmediği için motor 0.4.0. Eski 0.4.0 analizlerin tekrar edilebilirliği korunuyor.

## Testler ve sonuç analizi

**Python: 364 test geçti.** Önceki 338 test korundu, 26 yeni kontrol eklendi. Ruff ve biçim kontrolü temiz; satır+dal kapsamı **%97,74**. Bu oran Python paketinin kapsamıdır; arayüz için bir kapsam yüzdesi iddia edilmiyor.

Yeni Python kontrolleri oturum rolleri, yetkisiz erişim, HTML/JS/CSS sunumu, HEAD, CSP ve önbellek başlıkları, kaynak/config/map erişiminin kapalı olması, yol/symlink kaçışları, eksik derlemede güvenli503, gerçek API/şema eşitliği ve arayüz fikstürlerinin gerçek sözleşmelerle uyumunu doğruluyor. Panel sunum modülünde satır ve dal kapsamı %100.

**Arayüz: 31 test geçti.** Vitest ve Testing Library ile anahtarın yalnızca başlıkta taşınması, çıkış/geç yanıt, 30 saniyelik bekleme sınırı, güvenli hatalar, otomatik POST tekrarı olmaması, form doğrulaması, çift gönderim, sayfalama/filtre, 36/12/24 ayrımı, revizyon çakışması, gerekçe korunması, izinli durum geçişleri, yeniden analiz farkları, klavyeli sekmeler, eski raporlar, HTML içeriğinin metin olarak gösterimi, eksik veri/grafik boşluğu ve başarısız aktivasyon ayrımı kontrol edildi. Katı TypeScript, biçim kontrolü ve üretim derlemesi geçti. Testlerde taklit edilmemiş ağ istekleri engellendi.

**Gerçek tarayıcı:** macOS WebKit üzerinde geçersiz anahtar, yazıcı/okuyucu ayrımı, fan arızası analizi, rapor, telemetri, açık→inceleniyor→kapalı, yeniden analiz eşleşmesi, denetim geçmişi, 36 rol, eksik sensör verisi ve engellenmiş çalışma kontrol edildi. Yenilemede anahtarın temizlendiği görüldü. 375×812, 812×375 ve 1440×900 görünümlerinde sayfa yatay taşması oluşmadı; büyük tablolar kendi alanında kayıyor. Son kontrolde tarayıcı konsolunda uyarı/hata yoktu.

Tarayıcıda iki sunum kusuru yakalandı: dar grafikte yazıların fazla küçülmesi ve başarısız aktivasyon girişiminin “yürütülen ajan” sayısına karışması. Grafik genişliği uyarlanarak ve tamamlanan/başarısız adımlar ayrı gösterilerek düzeltildi; ilgili arayüz kontrolleri tekrar geçti.

Son dosya karşılaştırması, tekrarlanan kaynak kurulumunda setuptools `build/lib` altında eski bir hash'li JS dosyasının kalabildiğini gösterdi. Güncel HTML doğru dosyayı kullanıyordu ve temiz wheel etkilenmemişti; yine de kurulum artığı kabul edilmedi. Paketleme adımı yalnızca üretilmiş panel kopyasını yeniden oluşturarak düzeltildi. Eski dosya bilerek derleme alanına konup kaynak kurulumu tekrarlandı; kurulu paketin ve wheel'in dosya kümeleri/gövdeleri kaynak derlemeyle birebir karşılaştırıldı. Bu kontrol `scripts/verify_package.py` ile tekrar edilebilir.

**Gerçek HTTP:** İki profil ×11 senaryo =22 analiz, ayrı oturum rolleri, sıkı JSON sınırı, geçmiş, durum yönetimi, yeniden analiz, revizyon çakışması ve dört eşzamanlı yazma geçti. Panel HTML ve üç yerel varlığı aynı HTTP servisinden okunabildi; paket içinde anahtar bulunmadığı kontrol edildi. Python testlerinde sekiz eşzamanlı kayıt regresyonu da geçti.

**Kurulum:** `npm ci --offline` ile kilitli ön yüz kurulumu ve derleme geçti. Kayıt servisinin denetiminde bilinen npm güvenlik bildirimi sayısı sıfırdı; bu sonuç genel güvenlik garantisi değildir. Paket wheel/kaynak arşivi ve ayrı yalnızca çalışma zamanı Python ortamı ayrıca doğrulandı. Node/test bağımlılıkları olmadan panel varlıkları, CLI ve gerçek HTTP akışları çalıştı. Kaynak arşivinde ön yüz kaynağı, kilit dosyası ve testler bulunuyor; node_modules, özel yapılandırma ve veritabanı yok.

## Güncel katmanlar ve ajanlar

- **L1:** Sanal termal bölge ve arıza üretimi tamamlandı; gerçek cihaz yok.
- **L2:** Temel deterministik fan kontrol simülasyonu var; PLC programı ve kontrolör emniyeti henüz yok.
- **L3:** JSON ve yerel HTTP haberleşmesi hazır; OPC UA/Modbus adaptörü planlı.
- **L4:** SQLite, atomik kayıt, kaynak snapshot'ları, denetim, revizyon ve replay hazır; kurumsal hesaplar/PostgreSQL planlı.
- **L5:** Pilot termal model, sınırlı what-if ve MAE/RMSE hazır; saha kalibrasyonu yok.
- **L6:** Global Supervisor ve 12 uzman hazır; kalan24 rol ve grup koordinatörleri planlı.
- **L7:** CLI, API ve temel React inceleme paneli hazır. Ayrı geniş Digital Twin Lab ve Agent Workbench henüz yapılmadı.

Çalışır uzmanlar: **A02, A03, A06; B02, B03, B05, B06; D02, D06; F02, F03, F04.** Katalogdaki 36 rolün tek tek durumu `PROJECT_STATUS.md` içinde. Global Supervisor bu sayının dışında. Her olayda tüm12 rol çağrılmaz. Bakım ve PLC uzmanları planlıdır.

## Korunan çalışma ve sınırlar

Sprint4 kaynakları `../work/canovatwin-sprint-4-backup.zip` içinde korundu. Önceki raporlar değiştirilmedi. Git deposunda henüz commit olmadığı için yeni bir commit/uzak yedek varmış gibi raporlanmıyor. Test sunucuları ve özel test yapılandırması üretim verisine karıştırılmadı; doğrulama sunucuları kapatıldı.

Bu sprintin kabul ölçütlerinde açık hata veya yarım uygulama bırakılmadı. Bu, tüm olası hataların yokluğu anlamına gelmez. Tam tarayıcı/ekran okuyucu matrisi, üretim yükü, WCAG sertifikasyonu, gerçek şirket verisi, akademik teşhis doğruluğu ve fiziksel PLC doğrulaması bu teslimin dışındadır. Python3.12/3.13 ayrıca çalıştırılmadı; yerel doğrulama Python3.14.5, Node20.20.2 üzerinde yapıldı.

## Sonraki adım

**Digital Twin Lab:** kontrollü temel/arıza senaryolarını karşılaştırma, model parametrelerini görünür sınırlar içinde değiştirme ve deney sonuçlarını kayıtlı/tekrarlanabilir hale getirme. Yeni uzmanları sırf sayıyı büyütmek için açmadan önce deney ve değerlendirme disiplini güçlendirilecek. Gerçek PLC adaptörü Şubat2027 sonrası izinli donanımla, başlangıçta salt okunur ilerleyecek.

Kullanım ve yeniden test komutları `PANEL.md`, karar gerekçeleri `decisions-005-panel.md` içindedir.
