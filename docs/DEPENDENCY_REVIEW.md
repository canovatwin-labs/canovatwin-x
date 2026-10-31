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

## 31 Ekim: bütünleşik dal ve yeni güvenlik bulgusu

Sprint 10–12 ve onaylanan Vitest 5 değişikliği birleştirildi. Bu sırada yeni
GHSA-g3hv-75wg-m249 duyurusu, openapi-typescript 7.13.0 → Redocly 1.34.22 →
minimatch 5.1.9 zincirinde güvenlik kapısını durdurdu. Üretici 7.x'in kullandığı
Redocly iç arayüzleri güncel Redocly 2.x'in paket dışa aktarma sınırıyla uyuşmuyor.

Çalışan çözüm: yerel OpenAPI 3.1 belgesini işleyebilen openapi-typescript 6.7.6
sabitlendi; bu üreticinin HTTP yardımcısı yalnızca kendi bağımlılık dalında
undici 6.29.1'e sabitlendi. İlk denenen varsayılan 6.x kurulumu eski undici
nedeniyle ek güvenlik duyuruları taşıdığı için kabul edilmedi. Son kilitli
kurulumda tam npm audit **sıfır bulgu** döndürdü. `--default-non-nullable`
seçeneği önceki üreticinin varsayılan alan davranışını koruyor. Şema yeniden
üretimi, TypeScript, 39 panel testi ve üretim derlemesi geçti. Kaynak HTTP API
sözleşmesi değişmedi; üretilen TypeScript'in biçimi değişti.

Bu dar undici override'ı ve üretici major ertelemesi kalıcı bir uyumluluk
iddiası değildir. Yeniden yükseltme için üreticinin yamasız güvenli bağımlılık
zinciri, Node 22/24/26 uyumu, aynı OpenAPI belgesiyle üretim ve tüm kalite
kontrolleri gerekir. `--force`, peer bağımlılıklarını yok sayma veya audit
eşiğini düşürme kullanılmadı. #25'te plugin-react 6 tek başına Vite 7 ile
kurulamaz; Vite 8 geçişi birlikte değerlendirilmelidir.
