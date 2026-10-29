# CanovaTwin X

Veri merkezi soğutma ve çevresel izleme için kanıtlı arıza araştırma ve kalıcı analiz geçmişi çekirdeği. Bu sürüm sentetik telemetri üzerinde çevrimdışı çalışır. Python 3.12+ hedeflenir; yerel doğrulama macOS / Python 3.14.5 üzerinde yapılmıştır.

## İlk çalıştırma

Terminalde bu dosyanın bulunduğu `canovatwin-x` klasörüne geçin. `uv` ile kilitli kurulum:

```sh
uv sync --locked --extra dev --no-editable
.venv/bin/python scripts/check.py
.venv/bin/canovatwin --scenario fan_loss
.venv/bin/canovatwin --scenario sensor_missing
.venv/bin/canovatwin --registry
```

İlk bağımlılık kurulumu internet ister. Testler ve demo kurulumdan sonra çevrimdışı çalışır; API anahtarı, Docker, PostgreSQL veya yerel LLM gerekmez. Normal paket kurulumu kullanılır. Kaynak kodu değiştirdikten sonra CLI kopyasını yenilemek için:

```sh
uv sync --locked --extra dev --no-editable --reinstall-package canovatwin-x
```

Testler doğrudan `src` içindeki güncel kodu kullanır. `uv` yerine `python3 -m venv .venv` ve `.venv/bin/python -m pip install '.[dev]'` kullanılabilir; bu alternatif `uv.lock` sürümlerini sabitlemez.

## Güncel durum

Uygulama sürümü **0.7.0**, analiz motoru **0.4.0**. 12 uzmanlı çekirdek, yerel API ve React inceleme paneli çalışır durumda. Katmanlar ve tüm 36 rolün durumu `docs/PROJECT_STATUS.md`, son sprintin gerekçe ve test sonuçları `docs/SPRINT_6_REPORT.md` içinde.

## Ekip çalışması ve güvenlik

Katkı akışı [CONTRIBUTING.md](CONTRIBUTING.md), güvenlik ve açık bildirme
kuralları [SECURITY.md](SECURITY.md) içinde. İlk sürüm bir araştırma prototipidir;
şirket onayı, gerçek tesis doğrulaması veya üretime hazır olma iddiası taşımaz.
İlk plandaki açık işler ve öncelikler [ROADMAP.md](ROADMAP.md) içinde izlenir.
Organizasyon deposuna geçiş adımları [GITHUB_SETUP.md](GITHUB_SETUP.md) içinde.

## Ne çalışıyor?

- Özgün A01–F06 kataloğundaki 36 rol kayıtlı. Altı grup koordinatörü bu sayıya dahildir; Global Supervisor ayrıdır.
- **12 rol aktif:** A02, A03, A06, B02, B03, B05, B06, D02, D06, F02, F03, F04. Kalan 24 rol planlıdır.
- `mvp12` profilinde normal akışta 5, veri kalitesi yetersizse 4, anomalide kaynaklara göre 9–11 rol çalışır. `core6` karşılaştırma profilinde önceki 3/5/6 akışı korunur.
- Geçmiş eşleme, zayıf hipotezleri ayırma, kaynaklı yerel doküman arama, what-if ve MAE/RMSE kontrolü çalışır.
- Her rol yalnızca izinli deterministik aracını kullanır; görev, araç ve geçen süre bütçeleri uygulanır.
- Kanıt değerleri kaynak ölçümlerden tekrar hesaplanır. Doğrulanmamış bulgu veya değiştirilmiş rapor yayımlanmaz.
- İstatistik, hipotez, karşı kanıt, kaynak ölçüm kimlikleri ve ajan çalışma izleri JSON çıktısında bulunur.
- İsteğe bağlı SQLite kaydı: girdi, politika, sonuç, kanıt, ajan izi ve denetim geçmişi birlikte saklanır.
- Sıfır LLM çağrısı. Aktüatör komutu sözleşmede ifade edilemez; gerçek PLC adaptörü yoktur.

## Yerel API

```sh
.venv/bin/canovatwin-api init
.venv/bin/canovatwin-api
```

`init` anahtarları yalnızca yeni, özel izinli `.local/api-config.json` dosyasına yazar; mevcut dosyayı değiştirmez. Servis `127.0.0.1:8000` üzerinde çalışır. Canlılık `/health`, yerel OpenAPI `/openapi.json`; korumalı uçlar Authorization başlığı ister. Okuma ve yazma anahtarları ayrıdır. Analiz, senaryo, katalog, geçmiş, durum ve replay uçları `docs/API.md` içinde açıklanır. Panel `http://127.0.0.1:8000/panel/` adresindedir; yerel okuma/yazma anahtarıyla bağlanılır. Kullanım ve derleme adımları `docs/PANEL.md` içindedir.

Gerçek HTTP doğrulaması: `.venv/bin/python scripts/smoke_api.py`. Bu kontrol geçici sunucuyu sonunda kapatır. API ilk kurulumu bağımlılık indirmek için internet ister; çalışma sırasında bulut servisi/LLM gerekmez.

## Panel geliştirme ve ortak kalite kapısı

Çalıştırmak için Node gerekmez. Panel kaynağını geliştirmek/derlemek için Node 20.19+ ve ilk kurulumda internet gerekir:

```sh
cd web
npm ci
npm run check
cd ..
.venv/bin/python scripts/check.py --panel
```

Python ve panel testleri çevrimdışı çalışır. API sözleşmesi değişirse `web` içinde `npm run types` ile türleri yenileyin. Derlemeden sonra kurulu paketi yukarıdaki `--reinstall-package` komutuyla güncelleyin.

## Profil ve doküman seçimi

```sh
.venv/bin/canovatwin --profile mvp12 --scenario cooling_loss
.venv/bin/canovatwin --profile core6 --scenario cooling_loss
.venv/bin/canovatwin --profile mvp12 --scenario fan_loss --knowledge notes.json
```

Yeni üretilen senaryolar için varsayılan `mvp12`; bu profil üç açıkça işaretlenmiş demo notuyla başlar. `--knowledge` yerel JSON doküman dizisi okur; en fazla 200 KB, 8 doküman ve doküman başına 12000 karakter. Dokümanda `document_id`, `title`, `version`, `content` alanları gerekir; içerik özeti otomatik oluşturulur veya verilen özet doğrulanır. Arama sözcük tabanlıdır; LLM/semantik RAG yoktur.

`--input` kendi `research` alanını taşır; `research=null` eski altı rol akışını korur. JSON girişiyle ayrıca `--profile`/`--knowledge` verilemez. Geçmiş ve dokümanlar kayda dondurulur; replay canlı kaynak okumaz. Aynı ekipmanın geçmiş eşleşmesini görmek için önce eski başlangıç tarihli, sonra daha yeni başlangıç tarihli bir senaryoyu aynı `--db` ile çalıştırın.

## Demo ve giriş sözleşmesi

```sh
.venv/bin/canovatwin --scenario cooling_loss --format json --start 2026-10-28T00:00:00+00:00
.venv/bin/canovatwin --input request.json --format json
```

`--input`, `AnalysisRequest` sözleşmesine uygun bir JSON dosyası okur; en fazla 2 MB. `schema_version`, `window`, `as_of` ve `clock_mode` alanlarını kullanır. `window.samples` 3–600 ölçüm içerir; her ölçümde kimlik, saat dilimli zaman ve sözleşmedeki sensör alanları bulunur. Eksik sensör değeri `null` olarak ifade edilir. NaN, sonsuz, tanımsız alan ve `source=plc` reddedilir. Dosya adını, gerçek arıza etiketini veya senaryo adını ajan girdisine eklemeyin.

Varsayılan demo 120 örnek, bir saniyelik örnekleme ve `seed=42` kullanır. `--start` sabitlenirse telemetri ve teknik rapor yeniden üretilebilir; işlem süreleri doğal olarak değişir. Saat modu `replay` olduğundan son örnek zamanı simülasyonun inceleme saati kabul edilir. Canlı tesis ölçümü değildir.

Senaryolar: `normal`, `fan_loss`, `sensor_bias`, `sensor_missing`, `load_surge`, `cooling_loss`, `airflow_restriction`, `fan_mismatch`, `communication_loss`, `control_oscillation`, `combined`.

`completed` çalışmanın teknik olarak tamamlandığını belirtir. Rapor sonucu `clear`, `needs_review` veya `insufficient_data` olabilir. `blocked` doğrulama/yürütme hatasıdır; kullanılabilir nihai rapor üretilmez. CLI çıkış kodları: 0 tamamlandı, 1 çalışma engellendi veya tekrar sonucu farklı, 2 geçersiz giriş, 3 kayıt/geçmiş hatası. Bir arızanın bulunması tek başına işlem hatası değildir.

## Kalıcı geçmiş — Sprint 2

```sh
.venv/bin/canovatwin analyze --scenario fan_loss --start 2026-10-28T00:00:00+00:00 --db .local/history.sqlite3
.venv/bin/canovatwin history list --db .local/history.sqlite3
.venv/bin/canovatwin history list --db .local/history.sqlite3 --status open --format json
```

`--db` verilirse kayıt dosyası gerekirse oluşturulur. Verilmezse önceki demo davranışı sürer ve diske analiz kaydı yazılmaz. `history` okuma komutları eksik veritabanını oluşturmaz. Veritabanı hatası oluşursa başarılı kayıt raporu basılmaz.

Kalıcı analizde JSON çıktı, `run_id`, `request`, `policy` ve `result` içeren `RecordedAnalysis` nesnesidir; `--db` olmadan JSON çıktı önceki `AnalysisRun` biçimini korur. Aynı zaman penceresi ve politika aynı mantıksal olay kimliğini, her yürütme ayrı çalışma kimliğini alır.

Ayrıntı, durum değişimi ve tekrar çalıştırma örnekleri [geçmiş kullanım rehberinde](HISTORY.md). Bu sürümdeki yerel SQLite adaptörü PostgreSQL'e geçiş için bir repository arayüzünün arkasındadır; ek bağımlılık veya sunucu kurulumu gerektirmez.

## Kodun düzeni

Tek paket içindeki modüller, modüler monolitin ilk çekirdeğidir:

- `contracts.py`: sürümlü ve katı veri sözleşmeleri.
- `registry.py`, `agents.py`: özgün katalog, on iki uzman ve ortak fabrika.
- `state.py`, `policy.py`, `runtime.py`, `supervisor.py`: görev durumu, izinler, bütçe ve yönlendirme.
- `analysis/`: kalite, sinyal, hipotez, kaynak erişimi, eleştiri, simülasyon, kanıt doğrulama ve raporlama araçları.
- `telemetry.py`: indirgenmiş termal model ve etiketli senaryo üreticisi.
- `history.py`, `persistence/`: kalıcı kayıt, olay yaşam döngüsü, denetim izi ve tekrar çalıştırma.
- `api/`: sürümlü HTTP uçları, yerel anahtarlar, doğrulama, panel sunumu ve hata sözleşmeleri.
- `web/`: React/TypeScript panel kaynağı, kilitli bağımlılıklar, sözleşmeler ve arayüz testleri.
- `src/canovatwin/web/`: Python paketine dahil edilen çevrimdışı panel derlemesi.
- `history_cli.py`: geçmiş komutları; `identity.py`: runtime/depo için ortak olay kimliği.
- `tests/unit`, `tests/integration`, `tests/e2e`: otomatik doğrulama.
- `docs/`: mimari, geliştirme süreci ve sprint raporları.

Temel web paneli tamamlandı. Geniş Digital Twin Lab/Agent Workbench, PostgreSQL adaptörü, RAG ve LangGraph sonraki aşamalarda bu çekirdeğin çevresine eklenebilir. Boş servis klasörleri veya uygulanmış gibi görünen uzmanlar oluşturulmamıştır.

## Kapsam ve bilinen sınırlar

Bu sürüm örnek kurallarla aday neden üretir; öğrenilmiş veya LLM tabanlı bir teşhis modeli değildir. Tanımlı arızaların tümü benzersiz olarak ayırt edilemez. Özellikle fan performansı ve geri bildirim sorunu birden fazla aday üretir. Birleşik senaryo için tek bir kesin etiket yerine bileşen adayları gösterilir.

Kanıt doğrulaması hesapların ve bağlantıların tutarlılığını denetler; fiziksel nedenin doğrulandığı anlamına gelmez. Tesisle kalibrasyon ve akademik karşılaştırma henüz yapılmadı. Simülatörün nominal kapasite/debi değerleri değiştirilirse analiz politikasındaki nominal değerler de ilgili ekipman profiline göre ayarlanmalıdır.

Süre bütçesi araç çağrılarından önce/sonra denetlenir; çalışan bir Python fonksiyonunu zorla sonlandırmaz. Bu runtime yalnızca paket içindeki güvenilir araçları yürütür. Harici LLM veya eklenti eklenmeden önce iptal, süreç izolasyonu ve sağlayıcı zaman aşımı tasarlanmalıdır.

Şubat 2027 öncesi donanım bağımlılığı yoktur. Sonraki gerçek cihaz entegrasyonu uygunluk ve şirket iznine bağlı, başlangıçta salt okunur olacaktır.

## Yerel profil değerlendirmesi

```sh
.venv/bin/python scripts/evaluate_profiles.py --output .local/profile-evaluation.json
```

Bu komut iki profilde 11 senaryoyu üçer kez çalıştırır. Sonuçlar yerel sentetik davranış kontrolüdür; akademik teşhis doğruluğu veya tesis performansı benchmark'ı değildir. Model hata değerleri kalibre edilmemiş sentetik referansa göredir. Zayıf adaylar ilk B03 çıktısında korunur, nihai rapor ve what-if seçiminde eleştirmenin kararıyla ayrılır.

Dinamik deneyler: panelde sabit/dalgalı/toplu işlem yükü, ortam ve fan tepkisi ayarlanabilir. Model varsayımları ve sınırları `docs/SIMULATION.md` içinde açıklanır.
