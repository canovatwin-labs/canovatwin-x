# Yerel inceleme paneli

Panel, uygulama 0.6.0 ile aynı Python servisinden açılır. Motor 0.4.0 korunmuştur.
Çalışma sırasında internet, Node.js, ayrı bir ön yüz sunucusu veya LLM gerekmez.

## Kullanım

Proje klasöründe kilitli Python kurulumunu yapın:

```sh
uv sync --locked --extra dev --no-editable
.venv/bin/canovatwin-api init
.venv/bin/canovatwin-api
```

`init` yalnızca ilk kurulum içindir. Mevcut `.local/api-config.json` dosyasını silmeyin veya üzerine yazmayın. Yapılandırma zaten varsa doğrudan servisi başlatın. Tarayıcıda `http://127.0.0.1:8000/panel/` adresini açın. Özel yapılandırmada port değişmişse o portu kullanın.

Yerel yapılandırmadaki `read_token` ile geçmişi ve raporları okuyabilirsiniz. `write_token` ayrıca analiz, yeniden analiz ve durum değişikliğine izin verir. Anahtar bu servise gönderilir; URL, log, localStorage veya sessionStorage'a yazılmaz. Sayfa yenileme ve oturumu kapatma bellekteki oturumu temizler. Yerel yapılandırmayı ve anahtarları paylaşmayın.

### Ekranlar

- **Olay incelemeleri:** Durum filtresi, onarlı sayfalama, son rapor ve çalışma sayısı. Sayfadaki kayıt sayısı toplam olay sayısı olarak sunulmaz.
- **Yeni analiz:** 11 sentetik senaryo, core6/mvp12 profili, 30–600 örnek ve tam sayı tohum. Üretilen pencere ve analiz kaydedilir; sonuç ayrıntısına yönlendirilir.
- **Rapor:** Gözlemler, neden adayları, karşı kanıtlar, hipotez eleştirisi, kaynak alıntıları, geçmiş eşleşmeleri, model MAE/RMSE ve what-if hesapları. Eski çekirdek kayıtlarındaki boş araştırma alanı desteklenir.
- **Telemetri:** Giriş/referans sıcaklık, IT yükü/soğutma ve fan komutu/geri bildirim grafikleri ve tüm 11 sensör alanının tablosu. Eksik değerler “—”; çizgi `null` ve zaman boşluklarında kesilir. Yatay eksen gerçek geçen süredir.
- **Kanıtlar:** Metrik, değer/birim, üretici, kaynak türü ve ölçüm kimlikleri.
- **Ajan izi:** O çalışmadaki tamamlanan/başarısız adım kayıtları, araç sayıları, süre, hata kodu ve uzman çıktısı.
- **Geçmiş:** Çalışma seçimi, ayrı sayfalanan çalışma/denetim kayıtları, gerekçeler ve revizyonlar.
- **Ajan kataloğu:** 36 rol; 12 uygulanmış, 24 planlı. Global Supervisor ayrı gösterilir. Katalogdan uygulanmamış rol etkinleştirme yoktur.
- **Akış laboratuvarı:** Fiziksel senaryo ve aktarım profili ayrı seçilir. Kaydedilen sonuç kaynak/kabul/ret/düşen sayıları, sanal bağlantı ve tazelik, grafik, filtreli aktarım izi ve JSON indirme içerir. Olay raporu ve deney sonucu arasında iki yönlü bağlantı vardır. Kaydın adresi `#/stream/RUN_ID` biçimindedir; sayfa yenilenince yeniden oturum açılması gerekir.

İnceleme durumu analiz sonucundan bağımsızdır. Açık → inceleniyor, inceleniyor → açık/kapalı, kapalı → açık geçişleri vardır. Durum değişimi gerekçe ve beklenen revizyon ister. Çakışmada güncel revizyon alınır, yazılan gerekçe korunur ve işlem otomatik yeniden gönderilmez.

`completed` işlemin bittiğini belirtir; rapor ayrıca `clear`, `needs_review` veya `insufficient_data` taşır. `blocked` çalışmada rapor yerine engelleme nedeni görünür. Yeniden analiz sonuçları eşleşmeyebilir; farklar ayrıca gösterilir. HTTP başarısı bu ayrımları ortadan kaldırmaz.

Yazma isteğinde bağlantı koparsa kayıt yapılmış olabilir. Panel otomatik tekrar yazmaz; yeniden göndermeden önce olay geçmişini kontrol edin. Sekme kapatmak veya oturumu kapatmak, sunucuda başlamış analizi geri almaz.

## Ön yüz geliştirme

Kaynak `web/`, Python paketine giren derleme `src/canovatwin/web/` içindedir. Node.js 22.22.2+ (22.x) hedeflenir; Node 20.20.2 / npm 10.8.2 ile doğrulanmıştır.

```sh
cd web
npm ci
npm run types
npm run check
```

İlk `npm ci` internet ister. Paket kilidi depodadır. `types`, güncel kaynak API şemasını veritabanı açmadan dışa verir ve TypeScript sözleşmelerini üretir. Python `.venv` kurulumu gerekir. `npm run check`, biçim, katı tip denetimi, Vitest ve üretim derlemesini çalıştırır. `npm run dev` isteğe bağlıdır; `/api` isteklerini yerel 8000 portuna iletir.

Üretim derlemesi yerel servis altında `/panel/` tabanıyla çalışır. İnternet fontu, CDN, kaynak haritası, kullanıcı anahtarı veya şirket verisi pakete eklenmez. CSP aynı kaynak kod/stil/bağlantılarına izin verir; satır içi script/stil ve çerçeveleme kapalıdır. Paket yalnızca izinli dosya türlerini sunar.

Kaynak veya derleme değiştiğinde kurulu Python paketini güncelleyin:

```sh
uv sync --locked --extra dev --no-editable --reinstall-package canovatwin-x
.venv/bin/python scripts/check.py --panel
.venv/bin/python scripts/smoke_api.py
```

`check.py --panel` iki tarafın kalite kapısıdır. Python testleri TCP bağlantısını, arayüz testleri taklit edilmemiş fetch isteklerini engeller. Gerçek HTTP kontrolü geçici veritabanı ve sunucu kullanır, sonunda kapatır.

Paket oluştururken `uv build` kullanılır. `setup.py` doğrudan çalıştırılmaz; PEP517 derlemesi, önceki paketleme alanındaki eski panel varlıklarını otomatik temizler. Derlenen wheel'i kaynakla karşılaştırmak için `python scripts/verify_package.py WHEEL_DOSYASI` komutunu kullanın.

## Doğrulama sınırları

Tarayıcı kontrolü macOS yerleşik WebKit üzerinde yapıldı: varsayılan masaüstü görünümü, 375×812, 812×375 ve 1440×900 ekran boyutları. Sekmeler ok/Home/End tuşlarıyla çalışır; alanların görünür etiketleri ve odak işaretleri vardır. Büyük tablolar kendi bölgesinde kayar. Hareket azaltma CSS kuralı bulunur. Tam WCAG uygunluğu, ekran okuyucu sertifikasyonu veya tüm tarayıcılarda uyumluluk iddiası yoktur.

Bu panel kaydedilmiş analizleri gösterir. Sürekli canlı telemetri, alarm bildirimi, hesap yönetimi, ayrı Digital Twin Lab ve geniş Agent Workbench sonraki kapsamdır.

## Sprint 6: deney ve operasyon görünümü

Yeni analiz ekranında dinamik/reference modeli seçilir. Dinamik modelde sabit, dalgalı, toplu işlem yükü; temel IT yükü, ortam sıcaklığı ve fan zaman sabiti ayarlanır. Sağdaki brifing ve zaman çizelgesi planlanan deneyi açıklar; gerçekleşmiş tanı sonucu değildir. Varsayılan deney 360 örnektir.

Olay sayfasında üç sayaç yalnızca seçili filtrenin görüntülenen sayfasını özetler. Sayfadaki ilk olayın son çalışması, tesis şeması ve sıcaklık/güç eğrileriyle gösterilir. Bu ekran canlı izleme değildir. İletişim kaybında son ölçümün analiz saatine göre eskiliği gösterilir. Ayrıntıda aynı şema, kayıtlı deney ayarları ve ayrı fan grafiği vardır. Eksik ölçüm sıfıra çevrilmez.
