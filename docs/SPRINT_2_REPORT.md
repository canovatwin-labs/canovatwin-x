# Sprint 2 kapanış raporu — Kalıcı analiz geçmişi

**Tarih:** 28 Ekim 2026  
**Sürüm:** 0.3.0  
**Sonuç:** Kalıcı kayıt, olay yaşam döngüsü, geçmiş inceleme ve tekrar çalıştırma kabul ölçütleri tamamlandı.

## Amaç

Sprint 1'de bir sensör zaman penceresinden kanıtlı teknik rapora ulaşabiliyorduk. Ancak uygulama kapandığında bu sonuçlar yalnızca dışarı alınmış çıktılarda kalıyordu. Bu sprintin hedefi, analizleri girdileri ve çalışma koşullarıyla birlikte saklamak, eski sonuçları yeniden açmak ve mühendis inceleme sürecini kayıt altına almaktı.

## Yapılan işler ve gerekçeleri

### 1. Kalıcı kayıt katmanı

Python'ın yerleşik SQLite desteğiyle olay, analiz çalışması, kanıt, ajan izi ve denetim kayıtlarını saklayan bir depo eklendi. Böylece ek sunucu veya yeni üçüncü taraf bağımlılığı kurmadan çevrimdışı ilerleyebiliyoruz.

Depo `AnalysisRepository` arayüzünün arkasında tutuldu. Ajanlar doğrudan veritabanına erişmiyor; kayıt işleri uygulama hizmetinden yürütülüyor. İlk taslaktaki PostgreSQL hedefi korunuyor; bu sprintte önce veri sözleşmeleri ve bütünlük davranışları doğrulandı. PostgreSQL adaptörü henüz uygulanmadı.

### 2. Tek işlemle güvenli kayıt

Girdi, politika ve sonuç tam bir anlık görüntü olarak saklanıyor. Kanıtlar ve ajan izleri de aynı çalışma kimliğine bağlı tablolara yazılıyor. Tüm yazmalar tek transaction içinde: bir adım başarısızsa önceki adımlar da geri alınıyor.

Her yürütmeye yeni RUN kimliği veriliyor. Aynı girdi ve politika aynı INC kimliğini koruyor. Böylece bir olayın farklı çalışmaları birbirinin üstüne yazılmıyor. Aynı RUN kimliği ve aynı içerikle yapılan kayıt tekrarı ikinci kayıt üretmiyor; aynı kimlikle farklı içerik reddediliyor.

### 3. Olay yaşam döngüsü ve denetim izi

`open → investigating → closed` akışı, gerekçeli geri dönüş ve yeniden açma eklendi. Durum değişikliklerinde kullanıcı etiketi, gerekçe, zaman ve olay revizyonu kaydediliyor.

Her yeni analiz veya durum değişimi revizyonu artırıyor. Eski revizyona dayanarak gönderilen karar reddediliyor; böylece başka bir işlemden sonra güncel bilgi sessizce ezilmiyor. Kapalı olayın analizi tekrarlandığında olay kendiliğinden açılmıyor.

Normal sonuçlar da geçmişte saklanıyor. `open` bir inceleme durumudur; tek başına fiziksel arıza bulunduğu anlamına gelmez. Analizin teknik sonucu ayrıca gösteriliyor.

### 4. Kaydı doğrulayarak okuma

Tam çalışma okunurken JSON sözleşmesi, içerik özeti, metadata ve ayrı kanıt/ajan tablolarının tutarlılığı kontrol ediliyor. Bozuk içerik, beklenmeyen veri türü ve tutarsız tamamlanmış rapor kontrollü hata üretiyor.

Veritabanı şema sürümü ve uygulama kimliği denetleniyor. Başka uygulamaya ait veya daha yeni bir veritabanı değiştirilmeden reddediliyor. Okuma komutları eksik veritabanını oluşturmuyor.

SHA-256 özeti kazara değişiklikleri yakalamaya yardımcı olur; dosyaya yazma erişimi olan kişiye karşı dijital imza veya değiştirilemez denetim kaydı değildir.

### 5. Saklanan girdilerle yeniden çalıştırma

Geçmiş analiz, saklanmış ölçümleri, inceleme saatini ve politikayı kullanarak yeniden yürütülebiliyor. Yeni bir kayıt oluşturuluyor ve önceki kayda `replay_of` bağıyla bağlanıyor. Eski kayıt korunuyor.

Karşılaştırmada yalnızca ölçülen çalışma süreleri dışarıda bırakılıyor. Rapor, bulgular, kanıtlar, hata durumu ve izlerin diğer alanları farklıysa farklar gösteriliyor. Motor sürümü uyuşmuyorsa yeniden çalıştırma reddediliyor. Bu özellik tekrarlanabilirliği sınar; fiziksel teşhisin doğruluğunu tek başına kanıtlamaz.

### 6. Kullanım ve uyumluluk

`analyze --db`, geçmiş listeleme, olay özeti, çalışma ayrıntısı, denetim kaydı, durum değiştirme ve tekrar çalıştırma komutları eklendi. Önceki `--scenario` demo komutları ve kayıt seçilmediğinde kullanılan JSON sözleşmesi korundu.

`--db` ile kalıcı kayıt açıkça seçilir. Kayıt hatasında başarılı kayıt çıktısı basılmaz. Çıkış kodları çalışma, giriş ve depolama hatalarını ayırır. Kullanım örnekleri `HISTORY.md` içinde belgelendi.

## Aşama aşama doğrulama

- Başlangıç kalite kapısı: önceki **113 test geçti**; Sprint 1 kaynakları yedeklendi.
- Kalıcı kayıt ve yaşam döngüsünün ilk doğrulaması: **33 yeni test geçti**.
- Tekrar çalıştırma, geçmiş komutları ve ayrı süreçlerde kullanım: **29 yeni test geçti**.
- Bozuk veri türleri, açık ilk kurulum ve tutarsız rapor kaydına ilişkin son kontroller: **6 yeni test geçti**.
- Son bütünleşik kalite kapısı: **181 test geçti; başarısız test yok**.
- Satır ve dal kapsamını birlikte değerlendiren toplam kapsam: **%97,12**; proje alt sınırı %90.
- Ruff kod denetimi ve biçim kontrolü geçti.

Testler; yeniden açma, idempotent kayıt, geri alma, eski revizyon çakışması, kilitli veritabanı, salt okunur bağlantı, bozuk içerik, yetkisiz durum geçişi, kayıt izolasyonu, motor sürümü ve sonuç karşılaştırmasını kapsıyor. Ayrı süreçlerdeki uçtan uca kontroller de geçti.

## Paket ve temiz kurulum doğrulaması

Wheel ve kaynak dağıtımı üretildi. Wheel yeni, ayrı bir Python ortamına çevrimdışı kuruldu. Kurulu kaynakların çalışma kopyasıyla aynı olduğu ve paket/motor sürümlerinin 0.3.0 olduğu doğrulandı.

Kaynak klasörünün dışında, boşluk ve Türkçe karakter içeren geçici bir dizinden şu işlemler ayrı komut süreçleriyle sınandı:

- Aynı olaya iki ayrı çalışma kaydı oluşturma ve eski kaydı aynen geri okuma.
- İnceleme başlatma, kapatma, tekrar çalıştırma ve kapalı durumun korunması.
- Çalışma/denetim listeleri ve eski revizyonun reddedilmesi.
- Eksik veritabanının oluşturulmadan hata vermesi.
- Normal durum ve on arıza senaryosunun kurulu CLI ile çalışması.
- Geçersiz giriş çıkış kodu ve sıfır LLM/fiziksel komut sınırı.

Yerel doğrulama ortamı macOS / ARM64 / Python 3.14.5. Python 3.12/3.13, GitHub CI, ağ üzerinden çok kullanıcılı çalışma ve gerçek donanım bu oturumda test edilmedi.

## Korunan çalışma ve kapsam sınırları

Sprint 1'in kaynak yedeği proje alanındaki `work/canovatwin-sprint-1-backup.zip` dosyasında tutuldu. Çalışma yerel klasörde sürdürüldü; GitHub'a gönderim yapılmadı. Gerçek şirket verisi veya PLC bağlantısı kullanılmadı.

Aktif uzman sayısı altı olarak kaldı. Bu sprint yeni ajan sayısı artırmak yerine geçmiş olay uzmanlarının kullanabileceği kayıt temelini tamamladı. Şu kısımlar ileri kapsamda:

- PostgreSQL adaptörü ve ileri şema geçişleri.
- Kimlik doğrulama, rol bazlı servis erişimi ve web arayüzü.
- Otomatik yedekleme ve kurumsal veri koruma düzeni.
- Farklı zaman pencerelerini aynı fiziksel arızayla ilişkilendirme.
- On iki uzmanlı MVP, RAG, LLM ve gerçek PLC entegrasyonu.

Yerel `actor` alanı bir denetim etiketidir; doğrulanmış kullanıcı kimliği değildir. Veritabanı bekleme süresi ile analiz süre bütçesi farklı sınırlardır. SQLite adaptörü yerel, sentetik çalışma için doğrulandı.

## Yeniden çalıştırma

Proje klasöründe:

```sh
.venv/bin/python scripts/check.py
.venv/bin/canovatwin analyze --scenario cooling_loss --start 2026-10-28T00:00:00+00:00 --db .local/history.sqlite3
.venv/bin/canovatwin history list --db .local/history.sqlite3
```

Bir sonraki sprintin doğal başlangıcı, bu geçmişi kullanacak uzmanların ve 12 rollük çekirdeğe geçişin kabul ölçütlerini hazırlamaktır. Sprint 2'nin bilinen başarısız testi veya kapanmamış kabul kontrolü kalmadı.
