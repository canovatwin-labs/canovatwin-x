# Sprint 4 — Kontrollü API erişimi

## Amaç

On iki uzmanlı çekirdeği ve kalıcı geçmişi, gelecek web panelinin kullanacağı sürümlü FastAPI uçlarına açmak. Analiz algoritması ve motor sürümü korunacak; uygulama sürümü 0.5.0 olacak.

## Kabul ölçütleri

1. Önceki 242 testi ve kaynak yedeğini doğrula.
2. Analiz, senaryo, katalog, olay/çalışma/denetim geçmişi, durum değişimi ve replay uçlarını ekle.
3. Okuma/yazma erişimini ayır; istemci işlem sahibi taklit edemesin. Anahtarlar kaynak kodunda veya yanıtlarda bulunmasın.
4. Katı JSON sözleşmelerini koru; boyut sınırı, sayfalama, standart hatalar ve OpenAPI tanımları sağla.
5. Her API işlemi aynı iş parçacığında açılıp kapanan kendi SQLite bağlantısını kullansın. Eski kayıt ve replay davranışı korunsun.
6. Başarılı akışlar yanında yetki, bozuk giriş, çakışma, kayıt hatası, eşzamanlı istek ve kaynak sınırı testlerini geçir.
7. Temiz paket kurulumu ve gerçek yerel HTTP kontrolü yap; test sonuçlarını analiz et. Sprint/proje durum raporlarını güncelle.

Yerel servis varsayılan olarak yalnızca 127.0.0.1 üzerinde dinler. Bu sprint web ekranı, kurumsal hesap sistemi, uzak dağıtım, TLS, görev kuyruğu veya gerçek PLC eklemez. Erişim anahtarları yerel prototip için yetki sınırıdır; kurumsal kullanıcı kimliği değildir.

## Kapanış

- [x] 242 testlik başlangıç ve kaynak yedeği doğrulandı.
- [x] 12 HTTP yolu ve OpenAPI sözleşmesi eklendi.
- [x] Okuma/yazma yetkisi, gizli yapılandırma ve sunucu actor sınırı test edildi.
- [x] Katı/boyut sınırlı JSON ve hata davranışları test edildi.
- [x] Geçmiş/replay, bağlantı sahipliği ve eşzamanlı yazmalar doğrulandı.
- [x] Son kalite kapısı: 338 test, %97,70 kapsam, Ruff denetimleri geçti.
- [x] Gerçek loopback HTTP ve temiz runtime kurulumu geçti.
- [x] Sprint raporu, kullanım rehberi ve proje durumu tamamlandı.
