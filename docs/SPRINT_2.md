# Sprint 2 — Kalıcı olay, kanıt ve çalışma geçmişi

## Hedef

Altı ajanlı analiz çekirdeğinin sonuçlarını uygulama kapandıktan sonra yeniden açabilmek; aynı girdiyle yapılan farklı çalışmaları ayrı kaydetmek; olay inceleme durumunu gerekçeli, izlenebilir ve eşzamanlı değişikliklere karşı kontrollü yönetmek.

## Aşamalar ve kabul ölçütleri

1. Başlangıç kontrolü: Sprint 1 kaynaklarını koru, mevcut kalite kapısını geçir.
2. Kalıcı kayıt: SQLite deposunda girdi, politika, sonuç, kanıt ve ajan izlerini tek işlemde kaydet. Yeniden açma, geri alma, yinelenen kayıt, şema uyumluluğu ve bozuk veri kontrollerini test et.
3. Yaşam döngüsü ve tekrar çalıştırma: açık → inceleniyor → kapalı; gerekçeli yeniden açma, sürüm çakışması kontrolü ve denetim kayıtları. Saklanan girdi/politikayla yeni çalışma üret, önceki sonuçla süreler dışındaki farkları göster.
4. Kullanım: mevcut demo komutlarını koru; kayıt, geçmiş listeleme, ayrıntı, durum değişimi ve tekrar çalıştırma komutları ekle. Ayrı süreçlerde uçtan uca test et.
5. Kapanış: bütün testler, kod/biçim kontrolü, temiz paket kurulumu ve sprint raporu.

## Mimari tercih

Bu sprintte Python'ın yerleşik SQLite desteği kullanılacak. Böylece çevrimdışı/Mac üzerinde ek servis gerektirmeden veri bütünlüğü ve kullanım akışı doğrulanabilir. Repository arayüzü kalıcı kayıt katmanını analizden ayıracak; PostgreSQL hedefi ileri aşamada bu arayüzün adaptörü olarak ele alınacak. Bu seçim, önceki belgelerdeki PostgreSQL hedefinden geçici bir uygulama sırası değişikliğidir.

## Kapsam sınırı

Aktif uzman sayısı 6 olarak kalır. Bu altyapı sonraki geçmiş olay/bakım uzmanlarının temelidir. RAG, LLM, 12 uzman, web arayüzü ve gerçek PLC bu sprintte eklenmez. Olay kimliği mevcut girdi+politika özetini kullanır; farklı zaman pencerelerini tek fiziksel arızada birleştirmek ayrı çalışmadır. Yerel kullanıcı adı bir denetim etiketi olup kimlik doğrulama değildir.

## Kapanış

- [x] Başlangıç yedeği ve 113 testlik temel doğrulandı.
- [x] Kalıcı kayıt, işlem bütünlüğü ve yeniden açma test edildi.
- [x] Yaşam döngüsü, revizyon denetimi ve tekrar çalıştırma test edildi.
- [x] Eski komutlar korundu; yeni geçmiş komutları ayrı süreçlerde test edildi.
- [x] Son kalite kapısı: 181 test, %97,12 kapsam, Ruff denetimi/biçim kontrolü geçti.
- [x] Temiz kurulum ve kurulu CLI doğrulandı.
- [x] Gerekçeleri ve sınırlamaları içeren `SPRINT_2_REPORT.md` tamamlandı.
