# Sprint 16 — Kayıtlı koşum karşılaştırma API'si

31 Ekim 2026 · Uygulama 0.16.0 · Analiz motoru 0.4.0

## Hedef ve neden

Yol haritasındaki deney karşılaştırmasını, panelden önce test edilebilir bir
hesaplama ve API sözleşmesi olarak kurmak. Aynı ekipmana ait iki değişmez kaydın
ölçüm farkları görünür olmalı; bu işlem yeni analiz veya geçmiş kaydı üretmemeli.
İş kaydı: [#38](https://github.com/canovatwin-labs/canovatwin-x/issues/38).

## Yapılanlar

- `comparison.py`, veri erişiminden bağımsız betimleyici karşılaştırma üretir.
  On bir sensörde iki tarafın geçerli/eksik sayısı, minimum, maksimum, ortalama
  ve son ölçüm zamanındaki değerleri hesaplanır. Fark yönü aday − temeldir.
- Eksik son ölçüm önceki değerle doldurulmaz. Tamamen eksik sensöre sıfır veya
  uydurma sonuç atanmaz. Büyük sonlu değerlerde ortalama güvenli toplanır;
  sonlu sayı aralığını aşan fark açık hata verir.
- Sürümlü yanıt iki kayıt/olay kimliğini, ölçüm penceresini, motor/kaynak bilgisini,
  analiz durumunu ve varsa aktarım kabul/ret/kayıp sayaçlarını taşır. Engellenmiş
  analiz için rapor uydurulmaz. Üretim metadatası olmayan kaydın reçetesi tahmin edilmez.
- Değişen politika, araştırma snapshot'ı, üretim koşulu, aktarım profili ve telemetri
  alanları işaretlenir. Eşit olmayan ölçüm zamanları açıkça görünür.
- `GET /api/v1/comparisons` okuma anahtarıyla kullanılabilir. Farklı ekipman ve
  aynı kayıt 409, bulunamayan kayıt 404, geçersiz kimlik 422 ve anahtarsız istek
  401 verir. SQLite bağlantısı salt okunurdur; audit geçmişi değişmez.
- OpenAPI ve panelin üretilmiş tipleri güncellendi. Toplam HTTP yolu 17 oldu.
  Sözleşme ve örnek kullanım: [COMPARISON.md](COMPARISON.md).

## Testler ve gerçek sonuçları

- Tam kalite kapısı: **629 Python testi ve 50 mevcut panel testi geçti**.
  Ruff, biçim, TypeScript ve Vite üretim derlemesi temiz.
- Python toplam satır+dal kapsamı **%94,95**; yeni karşılaştırma modülü %100.
  Kapsam oranı tanı başarısı veya güvenlik garantisi değildir.
- **11 yeni test**: fark yönü, eksik son okuma, tamamen eksik kanal, engellenmiş
  analiz, büyük sayılar/taşma, zaman sırası ve saat farkı; motor/politika farkı,
  aktarım profilleri, replay eşitliği, kimlik/yetki, aynı/farklı ekipman, bulunamayan
  kayıt, tekrarlanabilir yanıt ve değişmeyen audit kayıtları.
- Temiz ortama kurulu 0.16.0 wheel üzerinden gerçek loopback HTTP: karşılaştırma,
  401/409 yolları ve mevcut 22 referans + 33 dinamik senaryo birleşimi, üç aktarım
  profili, varlık ayrımı, replay ve dört eşzamanlı yazma geçti.
- Wheel içindeki dört panel dosyası derlemeyle birebir eşleşti; eski dosya yok.
  MIT lisans metadatası ve lisans dosyası doğrulandı.
- Tam `npm audit`: 0 açık. Kilitli Python geliştirme bağımlılıkları için
  `pip-audit`: bilinen açık bulunmadı. Yeni bağımlılık eklenmedi.
- GitHub kalite matrisi Python 3.12/3.13/3.14, panel/paket ve bağımlılık denetimi
  PR üzerinde ayrıca çalışır; güncel uzaktaki sonuç için PR Checks kaydı esas alınır.

## Kapsamın durumu

L6 raporlama/API katmanına karşılaştırma sözleşmesi eklendi. L7 için tipler hazır;
**panelde koşum seçme ve yan yana karşılaştırma ekranı bu adımda yoktur**.
Yeni ekran eklenmediği için yeni görsel tarayıcı kabulü yapılmadı; mevcut panel
regresyonları ve paket dosyaları doğrulandı. Veri şeması ve analiz motoru değişmedi;
mevcut kayıt/replay yolu korundu. **12 uygulanmış / 36 kayıtlı uzman** ayrımı değişmedi.

Farklar betimleyicidir. Ortalama zaman ağırlıklı değildir; ölçümler hizalanmaz,
eksikler doldurulmaz ve kalite dışı değerler otomatik temizlenmez. Eşit olmayan
pencereler veya girdiler nedensellik çıkarımına izin vermez. Elektrik tasarrufu,
enerji integrali, PUE veya saha tanı başarısı hesaplanmaz. PLC bağlantısı yoktur.

## Sıradaki adım

Bu sözleşmeye bağlı panelden ekipman/koşum seçimi, yan yana ölçüm ve eksik veri
gösterimi, farklı girdi uyarıları ve izlenebilir dışa aktarma. Ana dala geçiş
Cansu dışındaki geliştiricinin incelemesi ve normal kalite kapısına bağlıdır;
onay kuralı atlanmaz.
