# 31 Ekim 2026 bütünleştirme raporu

Sprint 10–11'in akış ve günlük altyapısı, #33 ile ara dala alınan Sprint 12
AAU vaka çalışması ve ana daldaki Vitest 5 güncellemesi #31'de birleştirildi.
AAU birleştirmesinden önce kod ağacı onaylanan ara dalın ağacıyla birebir
karşılaştırıldı; kaynak kod farkı yoktu. Ana daldaki bağımlılık güncellemesi
ayrıca korundu. Squash geçmişinin oluşturduğu çakışmalar, daha yeni sprintin
sürüm ve şema çıktıları korunarak çözüldü.

İlk bütünleşik koşumda 549 Python ve 39 panel testi geçti. GitHub'ın üç Python
sürümü de geçti; yeni minimatch güvenlik duyurusu bağımlılık kapısını durdurdu.
Bu gerçek hata düzeltilmeden dal kapatılmadı. Ayrıntı ve son bağımlılık kararı:
[DEPENDENCY_REVIEW.md](DEPENDENCY_REVIEW.md).

Son yerel doğrulama: 549 Python testi, 39 panel testi; Python kapsamı %95,58.
Ruff, Prettier, TypeScript, panel derlemesi ve OpenAPI tip üretimi geçti.
Kilitli npm bağımlılıkları için tam audit sıfır bulgu verdi. Son commitin
GitHub kontrolleri ayrıca PR'da izlenir; eski commitin onayı yeni commit için
otomatik geçerli kabul edilmez. Dal koruması ve diğer geliştirici incelemesi
korunur.

Bu bütünleştirme yeni uzman eklemez: 36 kayıtlı rolden 12'si uygulanmıştır.
Gerçek PLC erişimi, ağ geçidi, saha kalibrasyonu ve bağımsız arıza teşhis
performansı hâlâ açık kapsamdır. #34'ün hastane veri denetimi ayrı PR'dır.
