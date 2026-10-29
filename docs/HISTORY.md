# Analiz geçmişi ve olay yaşam döngüsü

## Kalıcı kayıt oluşturma

```sh
.venv/bin/canovatwin analyze --scenario cooling_loss --start 2026-10-28T00:00:00+00:00 --db .local/history.sqlite3
.venv/bin/canovatwin history list --db .local/history.sqlite3
```

İlk komut giriş, politika, analiz sonucu, kanıtlar ve ajan izlerini tek veritabanı işlemiyle saklar. Yazma tamamlanamazsa bütün değişiklik geri alınır. Komut başarılıysa baştaki `RUN-...` çalışma kimliğini ve rapordaki `INC-...` olay kimliğini görebilirsiniz.

Her yürütme yeni bir RUN kimliği alır. Aynı girdi ve politika aynı INC kimliğini korur. İlk kayıt revizyon 1'dir. Sonraki kayıtlar ve durum değişiklikleri olay revizyonunu bir artırır. Normal sonuçlar da geçmişte tutulur; `open` inceleme durumudur, fiziksel arıza bulunduğu anlamına gelmez. Teşhis sonucu ayrıca `clear`, `needs_review` veya `insufficient_data` olarak görünür.

## Geçmişi inceleme

Aşağıdaki `INC-...` ve `RUN-...` değerlerini listede gördüğünüz gerçek kimliklerle değiştirin:

```sh
.venv/bin/canovatwin history show 'INC-...' --db .local/history.sqlite3
.venv/bin/canovatwin history runs 'INC-...' --db .local/history.sqlite3
.venv/bin/canovatwin history run 'RUN-...' --db .local/history.sqlite3
.venv/bin/canovatwin history audit 'INC-...' --db .local/history.sqlite3
```

JSON çıktısı için `--format json`; sayfalama için liste, çalışma listesi ve denetim kaydı komutlarında `--limit 20 --offset 0` kullanılır. Limit 1–100 arasındadır. `history list --status investigating` yalnızca incelenen olayları getirir. Listeler kayıt sırasına göre en yeniden eskiye döner; ekranda hiçbir satırın bulunmaması veri olmadığı veya sayfa sonuna ulaşıldığı anlamına gelebilir.

Liste/özet sorguları indekslenmiş alanları gösterir. Tam çalışma okunurken JSON şeması, içerik özeti (SHA-256), metadata ve ayrı kanıt/ajan kayıtlarının tutarlılığı denetlenir. Bozuk kayıtları düzeltme veya silme komutu yoktur; hata bildirilir ve veri korunur.

## İnceleme durumu

İzin verilen geçişler:

- `open` → `investigating`
- `investigating` → `closed` veya `open`
- `closed` → `open`

Doğrudan `open` → `closed` ve aynı duruma geçiş reddedilir. İncelemeyi kapatmak fiziksel arızanın teknik olarak doğrulandığını tek başına ifade etmez; gerekçede kararın dayanağı yazılmalıdır.

```sh
.venv/bin/canovatwin history transition 'INC-...' --to investigating --revision 1 --reason 'Sensör kayıtlarını incelemeye başladım' --actor local-user --db .local/history.sqlite3
```

`--revision` son olay özetindeki değer olmalıdır. Bu sırada başka analiz veya kullanıcı işlemi olayı değiştirmişse komut çakışma hatası verir. Yeni özeti okuyup kararınızı yeniden değerlendirerek güncel revizyonla çalıştırın. `--reason` boş bırakılamaz. Durum değişikliği ile denetim kaydı aynı işlemde yazılır.

`--actor` yerel denetim etiketidir; doğrulanmış kullanıcı kimliği veya yetki sistemi değildir. CLI etiketi kişisel kimlik doğrulaması değildir. 0.5.0 API ayrı okuma/yazma anahtarları ve sunucu tarafından belirlenen actor kullanır; kişisel kullanıcı yönetimi sonraki kapsamdadır.

## Analizi yeniden çalıştırma

```sh
.venv/bin/canovatwin history replay 'RUN-...' --db .local/history.sqlite3
```

Yeni sentetik veri üretilmez. Saklanan ölçümler, inceleme saati ve politika aynen kullanılır. Önceki kayıt korunur; yeni RUN kimliği `replay_of` ile kaynağa bağlanır. İki çalışmanın yalnızca ölçülen işlem süreleri karşılaştırma dışında kalır. Rapor, bulgular, kanıtlar, hata durumu ve izlerin diğer alanları farklıysa farklar gösterilir ve komut 1 koduyla çıkar. Aynı şekilde tekrar edilen engellenmiş çalışma da 1 döndürür.

Analiz motoru sürümü farklıysa yeniden çalıştırma reddedilir. Böylece farklı yazılım sürümleri yanlışlıkla aynı deney gibi sunulmaz. Motor davranışı değiştirildiğinde `version.py` ve paket sürümü birlikte artırılmalıdır.

Kapalı bir olayın analizi tekrarlandığında olay kendiliğinden açılmaz. Sonuçlar eski olay altında korunur ve revizyon ilerler. Yeni inceleme kararı gerekiyorsa gerekçeli `closed` → `open` geçişi yapılır.

## Veritabanı ve koruma sınırları

SQLite şema sürümü 1 ve uygulama kimliğiyle açılır. Boş dosyanın ilk kurulumu yalnızca açık oluşturma isteğiyle yapılır; tanınmayan/daha yeni şema ve başka uygulamaya ait veritabanı değiştirilmez. Şema, olaylar, çalışmalar, kanıtlar, ajan izleri ve denetim kayıtlarını içerir.

Yazmalar tek işlem ve yabancı anahtar denetimiyle yapılır. Aynı RUN kimliği ve aynı içerik tekrar gönderilirse ikinci kayıt oluşturulmaz; farklı içerikle aynı kimlik reddedilir. Kilitli depoda kontrollü hata verilir. Varsayılan SQLite bekleme süresi 5 saniyedir; bu, analiz supervisor'ının süre bütçesinden ayrı bir kayıt bekleme süresidir.

İçerik özeti kazara değişiklikleri tespit eder; dijital imza, şifreleme veya veritabanı dosyasına erişen kişiye karşı değiştirilemez denetim kaydı sağlamaz. Harici kullanıcı doğrulaması, ağ üzerinden çok kullanıcılı servis, otomatik yedekleme ve PostgreSQL bu sprintte uygulanmadı. Depo yerel ve sentetik veri için tasarlanmıştır.

Girdi+politika aynıysa tek olay oluşturulur; farklı zaman pencerelerini aynı fiziksel arızada birleştirme henüz yoktur. Bu sınırlama gelecekte olay korelasyonu tasarlanırken ele alınacaktır.

## Sprint 3 araştırma snapshot'ları

0.4.0 ile `mvp12` profili geçmiş vaka özetlerini, doküman sürüm/içeriklerini ve simülasyon ayarlarını `request.research` içinde saklar. Üretilen CLI senaryolarında uygun eski olaylar analizden önce seçilir. JSON girişi ve replay sırasında canlı geçmiş/doküman okuması yapılmaz. `core6` için `research=null` korunur; eski 0.3.0 olay kimlikleri bu ek alan nedeniyle değiştirilmez. Eski motor kayıtlarının okunması ile yeni motorla tekrar çalıştırılmaları ayrı işlemlerdir; sürüm uyuşmazlığında replay guard'ı geçerlidir.
