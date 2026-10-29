# Organizasyon deposu çalışma düzeni

Hedef organizasyon: **CanovaTwin Labs** (`canovatwin-labs`).
Depo: **canovatwin-x**, public ve MIT lisanslı. Ana dal: `main`.
Bu belge çalışma düzenini ve önerileri tanımlar; canlı sistemde doğrulanmış sonuçlar
[devir raporunda](GITHUB_HANDOFF_REPORT.md) ayrıca kaydedilir.

## Erişim ve hesaplar

- `mirackeser`: organizasyon sahibi ve ilk kaynak kodu yüklemesinin yazarı.
- `cansukalkan`: kendi hesabıyla katkı veren ekip üyesi; bu depoda Write yeterlidir.
- Organizasyon genelindeki erişim ayarları bu değişikliğin kapsamı dışındadır.
  Yeni özel depolarda erişim en az yetkiyle ayrıca belirlenmelidir.
- Her iki hesapta iki aşamalı doğrulama ve kurtarma kodlarının güvenli saklanması.
  Mevcut üyeleri çıkarabilecek bir 2FA kuralı önce hesaplar hazırlandıktan sonra uygulanır.
- GitHub CLI/SSH kimliği geliştiriciye özeldir. Hiçbir anahtar sohbete, Git
  uzak adresine, kaynak dosyasına veya commit mesajına yazılmaz.

## Depo ayarları

1. Public görünürlüğü, MIT lisansını ve organizasyon sahipliğini doğrulayın.
   Tüm commitler herkes tarafından okunabilir; özel veriler hiçbir dala eklenmez.
2. Mevcut Issues, Pull Requests, Discussions, milestone ve proje panosunu
   kullanın. Otomatik paket yayını veya deploy bu aşamanın kapsamında değildir.
3. Squash merge ve birleştirilmiş dalı otomatik silme günlük iş akışını sade tutar.
4. Actions varsayılan token izni read-only olmalı; PR oluşturma/onaylama izni
   gerekmemeli. Akışlar tam commit SHA'sına sabitlenir; PR kodu için
   `pull_request_target` veya self-hosted runner kullanılmaz.
5. Dependabot haftalık güncellemeleri inceleme PR'ı açar; otomatik merge yoktur.
6. Ücretli güvenlik ürünü, harcama limiti veya abonelik bu kurulumda açılmaz.

## Ana dal ve inceleme

Public depo için GitHub Free planında dal koruması kullanılabilir. `main` için
bir başka geliştiricinin onayı, son değişiklikte önceki onayın düşmesi ve başarılı
kalite kontrolleri gereklidir. Force push ve dal silme kapalı tutulur. Yönetici
istisnası varsa incelemeyi aşmak için kullanılmaz; gerçek ayarlar devir raporunda
belirtilir. Kendi PR'ını başka hesaba geçerek onaylamak bağımsız inceleme değildir.

Kaynak: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

## İlk yükleme ve doğrulama

İlk yükleme öncesi paylaşılacak dosyalar ve gizli bilgi taraması incelenir.
İlk commit mevcut sürümün tamamını içerir; geçmiş sprintler için yapay tarihçe
üretilmez. Yüklemeden sonra yerel/uzak commit kimliği, seçilen görünürlük,
dosya içeriği, gerçek CI sonucu ve erişim ayarları doğrulanır.

## Yeni geliştiricinin başlaması

```sh
gh auth login --hostname github.com --git-protocol https --web
gh repo clone canovatwin-labs/canovatwin-x
cd canovatwin-x
git config user.name KENDI_GITHUB_KULLANICI_ADINIZ
git config user.email KENDI_DOGRULANMIS_NOREPLY_ADRESINIZ
uv sync --locked --extra dev --no-editable
npm ci --prefix web
.venv/bin/python scripts/check.py --panel
git switch -c feat/kisa-is-adi
```

İki geliştirici kendi kimliğini kullanır; yer tutucu kimlikleri olduğu gibi
kopyalamaz. Ayrıntılı katkı ve inceleme akışı [CONTRIBUTING.md](../CONTRIBUTING.md).
