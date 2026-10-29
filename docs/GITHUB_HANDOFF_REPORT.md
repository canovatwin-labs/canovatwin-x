# GitHub düzeni ve kalite düzeltmesi — 30 Ekim 2026

## İnceleme sonucu

Depo `canovatwin-labs/canovatwin-x`, public ve MIT lisanslıdır. İlk kaynak
kaydı `mirackeser`, sonraki lisans ve topluluk belgesi kayıtları `cansukalkan`
kimliğiyle oluşturulmuştur. Mevcut lisans, changelog, Code of Conduct, iş
kayıtları, milestone'lar ve proje planı korunmuştur. İlk commit mesajında
0.1.0 geçse de paket sürümü 0.7.0'dır; geçmiş yeniden yazılmamıştır.

Bu düzenleme mevcut [PR #21](https://github.com/canovatwin-labs/canovatwin-x/pull/21)
üzerinden `cansukalkan` hesabıyla yayımlanır. Kendi PR'ını başka hesaba geçerek
onaylama veya dal korumasını aşarak birleştirme yapılmaz.

## Düzeltilen sorunlar

- Python 3.12'de OpenAPI sözleşmesi kontrolü başarısızdı: standart kütüphanenin
  413/422 açıklamaları Python 3.13+ ile farklıydı. API artık hata açıklamalarını
  açıkça tanımlar; bütün sürümler aynı sözleşmeyi üretir. Kontrol gevşetilmedi.
- MIT lisansı paket bilgilerine eklendi. Wheel içinde lisans metninin kaynakla
  aynı olduğu, source dağıtımında topluluk belgelerinin bulunduğu doğrulandı.
- Katkı, güvenlik ve GitHub rehberindeki eski private/lisans seçilmedi ifadeleri
  public/MIT durumuyla uyumlu hale getirildi.
- README'nin eksik rapor bağlantısı ve ayrıntılı kullanım belgesinin iki bozuk
  bağlantısı düzeltildi.

## Yerel doğrulama

- Python 3.14.5: **437 pytest testi geçti**, satır+dallanma kapsamı **%97,85**.
- Frontend: **39 test geçti**; biçim, TypeScript ve üretim derlemesi başarılı.
- Ruff ve GitHub Actions iş akışı denetimi (Actionlint): başarılı.
- Eklenen iki regresyon testi, Python 3.12 ve 3.13+ hata açıklamalarında bütün
  OpenAPI sözleşmesinin aynı kaldığını ve şema üretiminin veritabanı açmadığını doğrular.
- Ayrı ortamda kurulu wheel ile gerçek HTTP: **22 referans + 33 dinamik
  senaryo/profil birleşimi**, kimlik doğrulama, okuma/yazma ayrımı, geçmiş,
  olay durumu, replay, revizyon çatışması ve **4 eşzamanlı yazma** başarılı.
- Wheel: mevcut panelin 4 dosyası birebir aynı; MIT metadata ve LICENSE doğrulandı.
- Gitleaks: mevcut 8 commitlik erişilebilir geçmişte bulgu yok. Bu, tüm olası
  gizli bilgilerin bulunacağını veya ürünün güvenlik sertifikası olduğunu göstermez.

## GitHub durumu ve sınırlar

İncelemede Python 3.13/3.14 CI başarılı, 3.12 sözleşme kontrolü başarısızdı.
Bu düzeltmenin uzaktaki kontrol sonuçları PR'ın Checks alanından izlenir;
başarısız veya bekleyen kontrol başarılı sayılmaz.

- Secret scanning, push protection ve Dependabot security updates etkin.
- Actions token varsayılanı read-only; PR onaylama yetkisi kapalı.
- Ana dal başka bir geliştiriciden bir onay ister; yeni commit eski onayı düşürür.
  Force push ve silme kapalı. İnceleme başlangıcında zorunlu status check yoktu.
- Organizasyon genel izinleri değiştirilmedi. `cansukalkan` mevcut durumda
  organizasyon yöneticisidir; günlük katkı için Write yeterli olsa da bu işlem
  kullanıcının seçtiği yönetici rolünü değiştirmez.
- Organizasyonun zorunlu 2FA kuralı kapalıdır; bu bilgi tek tek hesapların 2FA
  durumunu göstermez. Kullanıcıları etkileyen genel ayarlar ayrı değerlendirilir.
- Beş Dependabot sürüm yükseltme PR'ı ayrı değerlendirme bekler. Bu değişiklik
  büyük sürüm yükseltmelerini otomatik birleştirmez.

## Sonraki adım

PR kontrolleri başarılı olduktan sonra `mirackeser` bağımsız incelemeyi yapar.
Ardından yeni ürün geliştirmesine geçilir: [yol haritasındaki](ROADMAP.md)
bağımsız değerlendirme ve gerçekçi simülasyon işleri, mevcut issue/milestone
planıyla eşleştirilir. Tamamlanmış yazılım testleri bağımsız teşhis başarısı
veya saha doğrulaması olarak sunulmaz.
