# Sprint 14 çalışma kaydı — 31 Ekim 2026

Bu dal, PR #25 ve #34 düzeltmeleri için ara verilen akış laboratuvarı
geliştirmesini korur. Henüz ana dala alınmış bir teslimat değildir.

Uygulananlar: dinamik fiziksel model üzerinde üç deterministik aktarım profili,
ayrı geliş/ölçüm saatleri, açık ret kodları, iz hash'i ve Pydantic tutarlılık
kontrolleri; kayıtlı reçete/iz/pencere, yeni `/api/v1/analyses/stream` yolu,
yeniden analizde metadata koruma; panelde form, kaydedilmiş sonuç bağlantısı,
grafik, sayfalanmış aktarım izi, ret filtresi ve JSON dışa aktarma.

Yerel tam kalite kapısı: **600 Python / 45 panel testi** geçti. 11 fiziksel
senaryo × 3 aktarım profili, örnek sınırları, kayıt sonrası uygulamayı yeniden
açma, bozuk iz, okuma/yazma yetkisi ve yeniden analiz sınandı. Tarayıcıda gerçek
HTTP ile kesintili fan kaybı deneyi kaydedildi: 120 kaynak ölçümünden 100'ü kabul,
20'si düşen ölçüm; iz ve grafik boşluğu görünür. Yetersiz veri sonucu korunuyor.

Kapanış öncesi kalan kabul işleri: bu dalı son onaylanmış `main` ve Vite 8
araçlarıyla birleştirmek, kurulu 0.14.0 wheel üzerinde genişletilmiş HTTP smoke
testini çalıştırmak, JSON indirme/dar-geniş ekran kontrolünü bitirmek, nihai
durum ve sprint raporlarını güncellemek ve son commit için GitHub CI almak.
Bu işler tamamlanmadan Sprint 14 tamamlandı denmez.
