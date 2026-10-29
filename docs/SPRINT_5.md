# Sprint 5 — Yerel operatör paneli

Başlangıç: uygulama 0.5.0 / motor 0.4.0; 338 test geçti, kapsam %97,70.
Önceki kaynaklar `../work/canovatwin-sprint-4-backup.zip` içinde korundu.

## Hedef ve kabul ölçütleri

- [x] React/TypeScript paneli aynı yerel API servisinden açılır; çalışma sırasında CDN veya Node sunucusu gerekmez.
- [x] Anahtar bellekte tutulur; okuma/yazma yetkisi sunucudan öğrenilir; çıkış/yenileme oturumu temizler.
- [x] 11 sentetik senaryo, core6/mvp12 profili, olay listesi/filtre/sayfalama gerçek API ile çalışır.
- [x] Raporda ölçümler, kanıtlar, adaylar, kaynaklar ve ajan izi görülebilir. Eksik veri/engellenmiş çalışma açıkça ayrılır.
- [x] Olay durumu gerekçe ve revizyonla değişir; replay sonucu ve değişiklikleri görünür.
- [x] Katalogda 36 rol ve uygulanmış/planlı ayrımı vardır; rol etkinleştirme gibi uygulanmamış kontroller yoktur.
- [x] Yükleme, boş liste, erişim/hata/çakışma, klavye ve dar ekran durumları doğrulanır.
- [x] Python regresyonları, arayüz testleri, tip denetimi, üretim derlemesi ve kurulu paket doğrulaması geçer.
- [x] Sonuç raporu ve güncel katman/ajan durumu yazılır.

Kapsam dışı: gerçek PLC, sürekli canlı telemetri, şirket verisi, yeni uzmanlar, LLM, çok kullanıcılı hesap sistemi, ayrı kapsamlı Digital Twin Lab/Agent Workbench.

Tasarım: Türkçe, açık çalışma yüzeyi ve koyu gezinme alanı, petrol yeşili vurgu, sistem yazı tipleri; anlam taşıyan etiketler ve görünür klavye odağı. Yerel çalışmaya uygun, dış kaynak çağrısı olmayan arayüz. React seçimi önceki yol haritasını izler.
