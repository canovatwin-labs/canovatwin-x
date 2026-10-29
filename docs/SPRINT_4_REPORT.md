# Sprint 4 kapanış raporu — Yerel API

**Tarih:** 28 Ekim 2026  
**Uygulama:** 0.5.0  
**Analiz motoru:** 0.4.0  
**Sonuç:** Kontrollü API erişimi kabul ölçütleri tamamlandı.

## Ne yapıldı, neden yapıldı?

Çalışan analiz çekirdeği ve kalıcı geçmiş, web panelinin kullanacağı sürümlü HTTP uçlarına açıldı. Ekranların doğrudan Python dosyalarını veya SQLite bağlantısını yönetmesi yerine, doğrulanan sözleşmelerle analiz başlatması ve sonuçları okuması mümkün oldu.

API aynı HistoryService ve SQLiteRepository katmanlarını kullanır. Bu sprintte analiz algoritması veya ajan sayısı değişmediği için motor sürümü 0.4.0 korundu; uygulama sürümü 0.5.0 oldu. Böylece motor uyumlu geçmiş çalışmalar için gereksiz replay uyuşmazlığı üretilmedi.

### API işlemleri

12 HTTP yoluyla servis canlılığı/hazırlığı, 36 rolün kataloğu, olay listesi/ayrıntısı, çalışma/denetim geçmişi, tam kayıt okuma, açık girdiden analiz, sentetik senaryo, inceleme durumu ve replay sunuldu. Liste uçları sınırlı sayfalama ve durum filtresi kullanır. JSON OpenAPI sözleşmesi yerel sunulur.

### Erişim sınırı

Ayrı okuma ve yazma anahtarları eklendi. Okuma anahtarı yazamaz; yazma anahtarı analizi ve durumu değiştirebilir. İşlem sahibi istemci gövdesinden alınmaz, sunucunun doğruladığı `api-writer` rolünden kaydedilir.

Başlatma yardımcısı anahtarları rastgele üretir, terminale yazmaz ve mevcut yapılandırmayı ezmez. Dosya izinleri 0600; yapılandırma `.local/` altında Git dışında tutulur. Servis yalnızca 127.0.0.1 üzerinde açılır. Bunlar yerel prototip yetkileridir; kişisel kurumsal hesap sistemi değildir.

### Sözleşmeler ve hata davranışı

Katı çekirdek modelleri gevşetilmeden, JSON tarih/dizi gösterimleri HTTP sınırında doğrulandı. Bilinmeyen alan, yanlış tür, NaN/sonsuz, saat dilimsiz zaman ve büyük gövde reddedilir. Gerçekte akan baytlar da gövde sınırına tabidir.

İstemci `actor` taklit edemez. Kısmi politika ayarı yalnızca belirtilen alanı değiştirir; mvp12'nin ajan bütçesini yanlışlıkla core6 varsayılanına düşürmez. OpenAPI'deki bütün referansların çözüldüğü test edildi.

Hatalar standart zarf, güvenli kod ve istek kimliğiyle döner. Ham girdi, anahtar veya SQL metni hata çıktısına eklenmez. Eski revizyon, yasak geçiş ve motor uyuşmazlığı 409; depo sorunu 503 olarak ayrılır. Kilitli depoda Retry-After verilir. Erken gövde reddi ve beklenmeyen hatalar için de izinli tarayıcının yanıtı okuyabilmesi sağlandı.

### Bağlantı ve kaynak yönetimi

Her API işlemi SQLite bağlantısını aynı iş parçacığında açıp kapatır. Testlerde eşzamanlı istekler ayrı bağlantılar kullanarak aynı olay altında kayıt biriktirdi; eski sonuçlar ezilmedi. Startup yabancı veya uyumsuz veritabanını dönüştürmeden reddeder. İçe aktarma tek başına veritabanı oluşturmaz.

Dış CDN gerektiren Swagger/ReDoc etkinleştirilmedi. OpenAPI JSON ve bütün API işlemleri kurulumdan sonra çevrimdışı kullanılabilir. Test istemcisinin deprecation uyarısı bastırılmadan desteklenen HTTPX2 bağımlılığına geçildi.

## Hangi testler yapıldı?

Aşamalı doğrulama:

- Başlangıçta önceki **242 test geçti**; Sprint 3 kaynak yedeği alındı.
- İlk API akışında **74 yeni test geçti**.
- Yapılandırma, OpenAPI ve tarayıcı sınırlarıyla birlikte 333 test geçti.
- Son kenar durumları ve politika profili kontrolüyle **338 test geçti**; önceki sürüme göre 96 yeni kontrol.
- Ruff kod ve biçim denetimleri geçti.
- Son toplam satır+dal kapsamı **%97,70**; proje alt sınırı %90.

Önemli davranış testleri:

1. **Yetki:** Eksik/yanlış anahtar 401, okuma anahtarıyla dört yazma işlemi 403. Yetkisiz girişte analiz kaydı oluşmadı.
2. **Tür ve kaynak sınırı:** JSON tarihleri ve dizileri doğru kabul edildi; metin olarak sayı, boolean sayı, NaN, bilinmeyen alan, yanlış içerik türü, büyük normal/akış gövdesi ve bozuk Content-Length reddedildi.
3. **Analiz:** Normal ve on arıza senaryosu HTTP üzerinden tamamlandı; core6/mvp12 profilleri korundu. Kontrollü bütçe engeli, sahte başarılı rapor yerine kayıtlı `blocked` sonuç verdi.
4. **Yaşam döngüsü:** İnceleme, kapatma, kapalı olayı replay etme ve eski revizyonu reddetme geçti; denetim sahibi sunucudan alındı.
5. **Geçmiş:** Uygulama yeniden başlatıldıktan sonra kayıt aynı içerikle okundu. Snapshot replay canlı kaynaklardan etkilenmedi. 0.3.0 örnek arşiv API'den okunabildi; farklı motor sürümüyle replay kontrollü reddedildi.
6. **Eşzamanlılık:** Test istemcisiyle sekiz eşzamanlı analiz ayrı RUN kimliği ve tek mantıksal olay altında kaydedildi. Kayıt/revizyon/audit sayıları doğrulandı.
7. **Hata gizliliği:** Bozuk kayıt, kilitli depo ve beklenmeyen hata güvenli yanıta dönüştü; özel içerik sızmadı.
8. **Tarayıcı:** Açık CORS kaynak listesi, yasak kaynak, erken 413 ve 500 yanıtlarının izinli kaynaktan okunması test edildi. Varsayılan CORS kapalıdır.
9. **Başlatma:** Yapılandırma dosya izni, farklı anahtarlar, mevcut dosyayı koruma, göreli depo yolu, anahtar gizleme ve yalnızca loopback bağlanma doğrulandı.

## Test sonuçlarının değerlendirmesi

Önceki 242 kontrolün korunması, API eklenirken çekirdek analiz ve kayıt davranışlarının bozulmadığını gösteriyor. Yeni 96 kontrol API sınırını, izinleri ve hata yollarını doğruluyor. Eşzamanlı testler bu yerel yükte SQLite bağlantılarının doğru sahiplenildiğini ve kayıt kaybı olmadığını gösterdi.

338 başarılı test fiziksel teşhis doğruluğu veya her üretim yükü için kapasite garantisi değildir. Bu sprintin ölçtüğü şey, mevcut sentetik çekirdeğe HTTP erişiminin doğruluğudur. Açık HVAC/şirket verisiyle akademik doğruluk veya üretim ölçeğinde yük deneyi yapılmadı.

Kapanış incelemesinde iki davranış özellikle düzeltildi ve test edildi: izinli tarayıcının erken/500 hata zarfını okuyabilmesi ve kısmi politika ayarının 12 ajan bütçesini koruması. Açık başarısız test bırakılmadı.

## Gerçek HTTP ve temiz paket

Servis geçici 127.0.0.1 portunda gerçekten başlatıldı. 22 profil/senaryo birleşimi, açık JSON analiz girişi, okuma/yazma yetkileri, geçmiş, durum değişimi, replay, revizyon çakışması, OpenAPI ve dört eşzamanlı yazma geçti.

İlk bağlantı açma denemesi çalışma ortamının yerel port izni nedeniyle engellendi; izinli loopback doğrulamasıyla gerçek HTTP testi tamamlandı. Bu bir uygulama testi hatası olarak gizlenmedi.

Wheel ayrı, yalnızca çalışma bağımlılıklarının bulunduğu boş Python ortamına kuruldu. Kurulu kaynaklar çalışma kopyasıyla karşılaştırıldı. Eski CLI profilleri, özel API yapılandırma oluşturma ve gerçek HTTP doğrulaması bu ortamda da geçti. Test sunucuları ve geçici veritabanları kapatılıp temizlendi.

Yerel ortam macOS / ARM64 / Python 3.14.5. Python 3.12/3.13, uzak CI, kurumsal ağ/TLS, gerçek PLC ve şirket verisi bu oturumda test edilmedi.

## Güncel durum ve sıradaki adım

12 uzman çalışıyor; katalogdaki diğer 24 rol planlı. Sanal cihaz, temel kontrol, termal/what-if model, kanıtlı analiz, kalıcı geçmiş, CLI ve yerel API var. Endüstriyel gateway ve gerçek cihaz bağlantısı yok. Web ekranı henüz yapılmadı.

Sıradaki sprint, bu API'yi kullanan web paneli olacak: senaryo/analiz başlatma, olay listesi, rapor ayrıntısı ve ajan çalışma izlerinin görüntülenmesi. Panelde analiz sonucu ile inceleme durumu ayrı gösterilecek; okuma/yazma yetkileri korunacak. Uygulama ve arayüz testleriyle, API entegrasyonu ve temel erişilebilirlik doğrulanacak.

Sprint 4'ün kabul ölçütleri tamamlandı. Kullanım rehberi `API.md`, tüm katman ve rollerin durumu `PROJECT_STATUS.md` içinde güncellendi. Çalışma yerel kaldı; GitHub'a gönderim yapılmadı.
