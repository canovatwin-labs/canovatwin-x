# Bağımlılık PR incelemesi — 30 Ekim 2026

PR #1–5, Dependabot tarafından açılmış ve bot tarafından imzalanmış bağımlılık
commitleridir. İlk proje yüklemesinin mirackeser tarafından yapılmasıyla çelişmez.
Botun yazarlığı değiştirilmez; insan düzeltmeleri kendi hesaplarıyla kaydedilir.

## Bulgular ve kararlar

- #1 setup-node 7.1.0, #2 checkout 7.0.1: resmi action sürümleri, tam SHA ile sabit.
  Eski Python 3.12/OpenAPI temel hatası dışında 3.13/3.14 kontrolleri geçti.
- #3 jsdom 30.1.3 ve #5 jest-dom 7.0.1: önceki 3.13/3.14 CI çalışmaları başarılı.
  Ana dal düzeltmesi alındıktan sonra üç sürümün tamamında tekrar doğrulanır.
- #4 TypeScript 7.0.2: gerçek bağımlılık uyuşmazlığı. Güncel
  openapi-typescript 7.13.0 yalnızca TypeScript ^5.x destekler; npm ci ERESOLVE verir.
  Bu PR ertelenir; [#22](https://github.com/canovatwin-labs/canovatwin-x/issues/22)
  compiler/generator geçişini ve yeniden etkinleştirme ölçütlerini izler.

TypeScript major güncellemeleri için dar kapsamlı Dependabot istisnası eklendi.
Diğer güncellemeler açık. --force/--legacy-peer-deps veya güvenlik kontrolünü
kapatma kullanılmaz. Paketleri yalnızca sürüm numarası büyüdüğü için birleştirmek
proje ilerlemesi sayılmaz.

## İnceleme kapısı

#21 ana dala alındıktan sonra #1/#2/#3/#5 güncel main ile yenilenir. Başarılı
Python 3.12/3.13/3.14, panel, paket ve bağımlılık kontrolleri gerekir. Her PR'ın
son commitindeki GitHub Checks sonucu esas alınır; geçmiş başarılı kontroller
son commit için başarı iddiası değildir. Ana dal değiştiğinde sıradaki PR yeniden
güncellenir ve doğrulanır. Uygun insan incelemesi olmadan ana dala yazılmaz.

Bu belge ilk triyajı kaydeder; nihai durum PR'ların canlı kontrol ve birleşme
kayıtlarında görülür. Büyük sürüm güncellemeleri otomatik olarak birleştirilmez.
