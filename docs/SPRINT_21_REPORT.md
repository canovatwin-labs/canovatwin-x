# Sprint 21 — Kanıtın zaman bağlamı ve ajan evrim planı

17 Kasım 2026 · Uygulama 0.19.0 / motor 0.4.0 üzerine artımlı geliştirme.

## Teslim

- Kanıt ayrıntısında sıcaklık, yük/soğutma ve fan kanalı seçimi.
- Tam kayıtlı pencere üzerinde yalnızca tekil kaynak kimliklerinin halkayla
  işaretlenmesi. Eksik kanal değeri, bulunamayan ve yinelenen kimlik için
  işaret üretilmez. Zaman boşlukları korunur; geçersiz zaman başlangıcı çizilmez.
- Grafik erişilebilir başlıkları dış kaynaklı kayıtları yanlışlıkla sentetik
  olarak adlandırmaz. Kaynak ölçüm tablosu ve ham kayıt incelemesi korunur.
- On ajan bileşeninin mevcut/planlı sınırları ve kabul kapıları
  `AGENT_EVOLUTION.md` içinde tanımlandı. Bu bileşenlerin tamamı uygulanmadı.
- Denetimde bulunan CVE-2026-126360 için opentelemetry-api kilidi 1.45.2'ye
  güncellendi; diğer bağımlılıklar topluca yükseltilmedi.
- Onaylı PR #48 ara dala birleştiği için Sprint 20 değişikliği main tabanına
  taşındı. Yeni PR doğrudan main'i hedefler.

## Doğrulama

- 632 Python testi geçti; satır+dallanma kapsamı %94,92.
- 88 arayüz testi geçti; 6 yeni kanıt-zaman testi dahil. Toplam 720 benzersiz test.
- Ruff, biçim, TypeScript ve üretim derlemesi geçti.
- Wheel: dört panel dosyası birebir, eski hash dosyası yok; MIT metadata kontrolü geçti.
- Kurulu wheel üzerinde gerçek HTTP: 22 referans + 33 dinamik birleşim, üç
  taşıma profili, yetki/geçmiş/yaşam döngüsü/replay ve dört eşzamanlı yazma geçti.
- npm audit ve kilitli geliştirme bağımlılıkları pip-audit: bilinen açık yok.
- Değişiklik taramasında Gitleaks hassas bilgi bulmadı.
- İzole masaüstü tarayıcıda salt okunur oturum, kayıtlı olay, kanıt seçimi,
  kanal değişimi ve kaynak halkaları görsel olarak kontrol edildi.
  Bu dilimde mobil cihaz/tarayıcı matrisi çalıştırılmadı.

## Sınırlar ve sıradaki adım

Model doğruluğu bu değişiklikle artırılmış veya yeniden ölçülmüş değildir.
12/36 uygulanmış uzman oranı (%33,3) toplam ürün tamamlanma oranı değildir.
Görünüm kayıtlı kaynak referanslarını gösterir; nedensellik veya arıza anı atamaz.

Sırada sürümlü görev zarfı ve deterministik yetenek yönlendirmesi var. Yerel
sözleşme testleri tamamlanmadan harici MCP/A2A/LLM servisleri açılmayacak.
Bağımsız PR incelemesi main birleştirmesinin kapısıdır. Ücretli model sağlayıcısı,
kurum verisinin dışarı aktarımı ve üretim PKI seçimi ileride ayrı karar gerektirir.
