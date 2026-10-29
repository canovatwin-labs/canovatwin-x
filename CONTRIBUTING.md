# Katkı ve inceleme düzeni

CanovaTwin X iki kişinin kendi GitHub kimliğiyle katkı verdiği bir ekip deposudur.
Hesap, parola, erişim anahtarı ve özel SSH anahtarı paylaşılmaz. Bir değişikliğin
yazarı onu yapan kişidir; başkasının adına commit oluşturulmaz.

## Bir değişikliğin akışı

1. Hedefi, kapsamı ve kabul ölçütlerini bir issue içinde yazın. Güvenlik
   açıklarını issue olarak paylaşmayın; `SECURITY.md` yolunu kullanın.
2. Güncel `main` üzerinden `feat/kisa-ad`, `fix/kisa-ad` veya `docs/kisa-ad`
   dalı açın. Aynı dosyadaki işleri önceden koordine edin.
3. Küçük, anlamlı commitler oluşturun. Örneğin `feat: add independent scenario evaluation`.
   Commit öncesi `git diff --cached` ile gönderilecek içeriği inceleyin.
4. `uv sync --locked --extra dev --no-editable` ve `web` içinde `npm ci`
   ardından `.venv/bin/python scripts/check.py --panel` çalıştırın.
   Paket/API değiştiyse `scripts/smoke_api.py` ve paket doğrulamasını da çalıştırın.
   `gitleaks git --redact` ile commit geçmişini tarayın.
5. Kendi dalınızı pushlayıp PR açın; neden, değişen davranış, test sonuçları ve
   bilinen sınırları şablona yazın. Diğer geliştiriciden inceleme isteyin.
6. Testler ve diğer geliştiricinin incelemesi tamamlandıktan sonra birleştirin.
   `main` üzerinde force push ve doğrudan geliştirme yapmayın.

İlk yükleme mevcut 0.7.0 sürümünün tek başlangıç kaydıdır; geçmiş sprintler için
geriye dönük yapay commitler veya gerçekte çalışılmamış katkılar oluşturulmaz.

## Kimlik ve erişim

Her geliştirici kendi bilgisayarında `git config user.name` ve `git config
user.email` değerlerini kendi hesabına göre ayarlar. GitHub'ın doğrulanmış
`noreply` adresi kullanılabilir. `git author` ile push yapan hesabın kimliği
farklı kavramlardır; kimlik doğrulama herkesin kendi hesabıyla yapılır.

Hedef erişim: `mirackeser` organizasyon sahibi; `cansukalkan` organizasyon üyesi
ve yalnızca bu depoda Write. Günlük geliştirme için Admin yetkisi gerekmez.
Bu belge kendi başına GitHub üzerinde yetki veya dal koruması etkinleştirmez.
Depo public olduğu için GitHub Free planında dal koruması kullanılabilir.
`main` bir başka geliştiricinin onayını gerektirir. Başarılı CI kontrolünün
zorunlu olup olmadığı canlı depo ayarlarından ayrıca doğrulanır.

## Veri ve kapsam

- Yalnızca sentetik veya paylaşım izni doğrulanmış örnekler commitlenir.
- `.local`, `.env`, anahtarlar, gerçek tesis verisi, günlükler ve veritabanları
  gönderilmez. `.gitignore` tek başına gizli bilgi denetimi değildir.
- LLM çağrısı ve fiziksel cihaz komutu mevcut kapsamda yoktur.
- Sprint raporu, çalışan/planlanan rol ayrımı ve test kanıtı her teslimde güncellenir.
- Proje public olarak [MIT lisansı](LICENSE) altında yayımlanır. Üçüncü taraf
  içerik ve bağımlılıklar kendi lisanslarına tabidir; kaynakların kullanım
  ve paylaşım izinleri ayrıca doğrulanır.

Ayrıntılı kapanış kapısı: [DEVELOPMENT.md](docs/DEVELOPMENT.md).
