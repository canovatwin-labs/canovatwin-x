# Organizasyon deposu çalışma düzeni

Hedef organizasyon: **CanovaTwin Labs** (`canovatwin-labs`).
Hedef depo: **canovatwin-x**, private. Ana dal: `main`.
Bu belge hedef ayarları tanımlar; canlı sistemde doğrulanmış sonuçlar
[devir raporunda](GITHUB_HANDOFF_REPORT.md) ayrıca kaydedilir.

## Erişim ve hesaplar

- `mirackeser`: organizasyon sahibi ve ilk kaynak kodu yüklemesinin yazarı.
- `cansukalkan`: kendi hesabıyla katkı veren ekip üyesi; bu depoda Write yeterlidir.
- Organizasyon varsayılan depo erişimi: None. Üyelik tek başına tüm depolara
  erişim vermemeli; erişim depo veya ekip üzerinden açıkça atanmalıdır.
- Her iki hesapta iki aşamalı doğrulama ve kurtarma kodlarının güvenli saklanması.
  Mevcut üyeleri çıkarabilecek bir 2FA kuralı önce hesaplar hazırlandıktan sonra uygulanır.
- GitHub CLI/SSH kimliği geliştiriciye özeldir. Hiçbir anahtar sohbete, Git
  uzak adresine, kaynak dosyasına veya commit mesajına yazılmaz.

## Depo ayarları

1. Private görünürlüğü ve organizasyon sahipliğini doğrulayın.
2. Issues ve Pull Requests kullanın; henüz gerekmeyen Wiki/Pages/Discussions
   servislerini açmayın. Otomatik yayın veya deploy bu aşamanın kapsamında değildir.
3. Squash merge ve birleştirilmiş dalı otomatik silme günlük iş akışını sade tutar.
4. Actions varsayılan token izni read-only olmalı; PR oluşturma/onaylama izni
   gerekmemeli. Akışlar tam commit SHA'sına sabitlenir; PR kodu için
   `pull_request_target` veya self-hosted runner kullanılmaz.
5. Dependabot haftalık güncellemeleri inceleme PR'ı açar; otomatik merge yoktur.
6. Ücretli güvenlik ürünü, harcama limiti veya abonelik bu kurulumda açılmaz.

## Dal koruması sınırı

GitHub Free organizasyonlarda private depolar için korumalı dal özelliği yoktur.
GitHub Team/Enterprise erişimi sağlanırsa `main` için bir onay, son değişiklikten
sonra eski onayın düşmesi, çözümlenmiş konuşmalar ve başarılı Quality kontrolleri
zorunlu kılınmalı; force push/silme engellenmelidir. Ücretli plan yokken bunlar
ekip prosedürüdür, sunucu tarafından zorlanan güvenlik kontrolü değildir.

Kaynak: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

## İlk yükleme ve doğrulama

İlk yükleme öncesi paylaşılacak dosyalar ve gizli bilgi taraması incelenir.
İlk commit mevcut sürümün tamamını içerir; geçmiş sprintler için yapay tarihçe
üretilmez. Yüklemeden sonra yerel/uzak commit kimliği, private görünürlük,
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
