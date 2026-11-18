# Sprint 22 — Yerel ajan görev sözleşmesi

18 Kasım 2026. Temel sürüm, #55'in birleştirildiği main dalıdır.

Supervisor, sonraki görevi çıktı yeteneğine göre seçer. Katalog bir yetenek
için tek etkin ve deterministik uzman sağlayabilir. TaskEnvelope v1 sürüm,
yetenek, olay kimliği ve görev kimliği taşır. Yerel kabul, olay kapsamı ile
atanan uzmana ait görev kimliğini denetler ve bir analizde ikinci kabulü engeller.
Görev kimliği biçimi ve kayıtlı iz sözleşmesi önceki analizlerle uyumludur.

Yürütme bütçesi öncesinde ve sonrasında süre ve iptal kontrol edilir. İptal
işbirliklidir ve çalışan bir hesaplamayı ortasında kesmez. Görev kabul kaydı
tek analiz süresince bellekte tutulur. Harici taşıma için kalıcı tekrar teslim
koruması ve servis kimliği ayrı adımda uygulanacaktır.

- 643 Python testi ve 88 panel testi geçti. Python satır ve dallanma kapsamı %95,04.
- 11 yeni test sürüm, şema, kapsam, çift teslim, planlı rol, belirsizlik, döngü
  ve iptal davranışlarını kapsar. Mevcut süre sınırı testleri de geçti.
- Kurulu wheel, statik varlıklar ve MIT bilgileri doğrulandı. Gerçek HTTP üzerinden
  55 senaryo birleşimi, üç taşıma profili ve yetki, tekrar analiz, geçmiş,
  yaşam döngüsü ve eşzamanlı kayıt kontrolleri geçti.
- Python ve üretim npm bağımlılığı taramaları temiz. Tam npm taraması geliştirme
  araçlarındaki picomatch için
  [CVE-2026-112366](https://github.com/advisories/GHSA-fc5q-39xc-vjpf) bildiriyor.
  Duyuruda yamalı sürüm listelenmiyor. CI güvenlik denetimi korunuyor.

Uygulanan uzman sayısı 12/36 (%33,3). Yeni model doğruluğu değerlendirmesi
yapılmadı. Sıradaki dilim için önce güvenlik bulgusu kapatılır. Ardından görev
sözleşmesine bağlı ilk harici adaptör için taşıma ve servis kimliği seçilir.
