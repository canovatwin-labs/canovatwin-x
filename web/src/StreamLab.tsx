import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { Session } from './App';
import type { RecordAnalysis, Schema } from './api/types';
import { Badge, Empty, ErrorNotice, Loading, PageHeading, Pager, Stat } from './components';
import { ConditionsForm, defaultConditions } from './Experiment';
import { useLoad } from './hooks';
import { date, number, scenarios } from './labels';
import { TelemetryChart } from './Telemetry';

const deliveries = {
  ordered: ['Düzenli aktarım', 'Her ölçüm 200 ms gecikmeyle ulaşır; aktarım kaybı eklenmez.'],
  jitter: [
    'Gecikme ve tekrar',
    '0,1–6 sn gecikme ve her 17 ölçümde bir tekrar. Geç kayıtlar reddedilebilir.',
  ],
  outage: [
    'Bağlantı kesintisi',
    'Deneyin üçte biri ile yarısı arasında bağlantı kesilir; o ölçümler düşer.',
  ],
} as const;
const outcomes: Record<string, string> = {
  accepted: 'Kabul',
  rejected: 'Ret',
  dropped: 'Düştü',
  disconnect: 'Bağlantı kesildi',
  reconnect: 'Yeniden bağlandı',
  flush: 'Tampon kesinleştirildi',
};
const reasons: Record<string, string> = {
  late: 'Zaman sınırından sonra ulaştı',
  duplicate_id: 'Tekrar ölçüm kimliği',
  duplicate_timestamp: 'Tekrar ölçüm zamanı',
  disconnected: 'Bağlantı kapalı',
  future: 'Gelecek tarihli ölçüm',
  arrival_clock: 'Geliş saati geriye gitti',
  buffer_full: 'Tampon dolu',
};

export function StreamLab({ session }: { session: Session }) {
  const [scenario, setScenario] = useState<Schema['StreamBody']['scenario']>('normal');
  const [delivery, setDelivery] = useState<keyof typeof deliveries>('jitter');
  const [count, setCount] = useState('120');
  const [seed, setSeed] = useState('42');
  const [conditions, setConditions] = useState(defaultConditions);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const locked = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const writer = session.principal.role === 'writer';
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (locked.current || !writer) return;
    if (
      !count.trim() ||
      !seed.trim() ||
      !Number.isSafeInteger(Number(count)) ||
      Number(count) < 30 ||
      Number(count) > 600 ||
      !Number.isSafeInteger(Number(seed))
    ) {
      setError(new Error('Örnek sayısı 30–600 arasında, tohum ise güvenli bir tam sayı olmalı.'));
      return;
    }
    if (
      Object.values(conditions).some(
        (value) => typeof value === 'number' && !Number.isFinite(value),
      )
    ) {
      setError(new Error('Çalışma koşullarını doldurun.'));
      return;
    }
    locked.current = true;
    setBusy(true);
    setError(undefined);
    try {
      const record = await session.api.streamExperiment({
        profile: 'mvp12',
        start: null,
        scenario,
        delivery,
        count: Number(count),
        seed: Number(seed),
        conditions,
      });
      if (mounted.current) window.location.hash = `/stream/${record.run_id}`;
    } catch (issue) {
      if (mounted.current) setError(issue);
    } finally {
      locked.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <>
      <PageHeading kicker="TELEMETRİ / AKTARIM DENEYİ" title="Akış laboratuvarı">
        Fiziksel arıza ile veri aktarımını ayrı seçin; yalnızca kabul edilen ölçümler analiz
        edilsin.
      </PageHeading>
      {!writer && (
        <p className="notice warn">
          Salt okunur oturum. Deney oluşturmak için yazma yetkisi gerekiyor.
        </p>
      )}
      <div className="form-layout">
        <section className="card">
          <h2>Deney reçetesi</h2>
          <p className="muted">Dinamik model · 1 sn örnekleme · Sanal saat</p>
          {error !== undefined && <ErrorNotice error={error} />}
          <form onSubmit={submit}>
            <fieldset disabled={busy || !writer}>
              <label htmlFor="stream-scenario">Fiziksel senaryo</label>
              <select
                id="stream-scenario"
                value={scenario}
                onChange={(e) => setScenario(e.target.value as typeof scenario)}
              >
                {scenarios.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
              <label htmlFor="stream-delivery">Aktarım profili</label>
              <select
                id="stream-delivery"
                value={delivery}
                onChange={(e) => setDelivery(e.target.value as typeof delivery)}
              >
                {Object.entries(deliveries).map(([id, [name]]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
              <p className="hint">{deliveries[delivery][1]}</p>
              <div className="form-row">
                <div>
                  <label htmlFor="stream-count">Örnek sayısı</label>
                  <input
                    id="stream-count"
                    type="number"
                    min="30"
                    max="600"
                    step="1"
                    required
                    value={count}
                    onChange={(e) => setCount(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="stream-seed">Rastgelelik tohumu</label>
                  <input
                    id="stream-seed"
                    type="number"
                    step="1"
                    required
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                  />
                </div>
              </div>
              <ConditionsForm value={conditions} onChange={setConditions} />
              <button className="primary wide" disabled={busy || !writer}>
                {busy ? 'Deney çalışıyor ve kaydediliyor…' : 'Aktarım deneyini çalıştır ve kaydet'}
              </button>
            </fieldset>
          </form>
        </section>
        <aside className="stack">
          <article className="card experiment-card">
            <p className="eyebrow">ÖLÇÜMDEN ANALİZE</p>
            <h2>Veri yolu da deneyin parçası</h2>
            <ol className="stream-stages">
              <li>
                <b>01 / Fiziksel model</b>
                <p>İş yükü, fan ve soğutma gecikmeleriyle sentetik ölçümler üretilir.</p>
              </li>
              <li>
                <b>02 / Aktarım</b>
                <p>{deliveries[delivery][1]}</p>
              </li>
              <li>
                <b>03 / Toplayıcı</b>
                <p>
                  2 sn gecikme toleransı. Tekrar ve geç ölçümler gerekçeyle ayrılır. Eksikler
                  doldurulmaz.
                </p>
              </li>
              <li>
                <b>04 / Uzman incelemesi</b>
                <p>
                  Kesinleşmiş pencere 12 uzmanlı profille değerlendirilir; reçete ve tüm aktarım izi
                  kayda eklenir.
                </p>
              </li>
            </ol>
          </article>
          <div className="notice neutral">
            <b>Çevrimdışı, hızlandırılmış tekrar.</b> Buradaki bağlantı ve tazelik sanal saate
            aittir. Fiziksel ağ veya PLC bağlantısını göstermez.
          </div>
        </aside>
      </div>
    </>
  );
}

export function StreamRun({ session, id }: { session: Session; id: string }) {
  const [refresh, setRefresh] = useState(0);
  const loaded = useLoad(() => session.api.run(id), [session.api, id, refresh]);
  return (
    <>
      <PageHeading
        kicker="KAYITLI AKTARIM DENEYİ"
        title="Akış sonucu"
        action={
          <a className="button secondary" href="#/stream">
            Yeni aktarım deneyi
          </a>
        }
      >
        Kaydedilmiş sanal saat, ölçüm kabulü ve analiz bağlantısı.
      </PageHeading>
      {loaded.loading ? (
        <Loading />
      ) : loaded.error !== undefined ? (
        <ErrorNotice error={loaded.error} retry={() => setRefresh((v) => v + 1)} />
      ) : (
        loaded.data && <StreamResult key={id} record={loaded.data} />
      )}
    </>
  );
}

export function StreamResult({ record }: { record: RecordAnalysis }) {
  const [exceptions, setExceptions] = useState(true);
  const [offset, setOffset] = useState(0);
  const experiment = record.stream_experiment;
  if (!experiment)
    return (
      <Empty>
        Bu çalışma bir aktarım deneyi içermiyor.{' '}
        <a href={`#/incidents/${record.result.incident_id}`}>Olay raporuna geç</a>
      </Empty>
    );
  const { accepted, rejected, dropped, generated, final_state: state, recipe } = experiment;
  const events = experiment.events.filter((event) => !exceptions || event.outcome !== 'accepted');
  const page = events.slice(offset, offset + 10);
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' }),
    );
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${record.run_id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return (
    <>
      <section className="card stream-summary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{deliveries[recipe.delivery][0]}</p>
            <h2>{experiment.window.asset_id}</h2>
          </div>
          <div className="actions">
            <Badge value={record.result.report?.status ?? record.result.status} />
            <a className="button primary" href={`#/incidents/${record.result.incident_id}`}>
              Kanıt ve raporu aç
            </a>
            <button className="secondary" onClick={download}>
              Deneyi JSON indir
            </button>
          </div>
        </div>
        <div className="stream-pipeline" aria-label="Ölçüm kabul özeti">
          <Stat
            title="Kaynakta üretilen"
            value={generated}
            detail={`${recipe.generation.count} sn planlanan fiziksel deney`}
          />
          <Stat
            title="Kabul edilen"
            value={accepted}
            detail="Analize verilen kesinleşmiş ölçümler"
          />
          <Stat
            title="Reddedilen paket"
            value={rejected}
            detail="Geç veya tekrarlanan gelişler dahil"
          />
          <Stat
            title="Aktarımda düşen"
            value={dropped}
            detail="Sanal kesintide gönderilmeyen ölçümler"
          />
        </div>
        <p className="hint">
          Ret sayısı tekrar gönderimleri de içerir; üretilen ölçüm sayısından çıkarılarak kayıp
          oranı hesaplanmaz.
        </p>
      </section>
      <div className="stream-result-grid">
        <section className="card">
          <TelemetryChart samples={experiment.window.samples} />
          <p className="hint">
            Grafik yalnızca kabul edilen ölçümleri gösterir; zaman boşlukları çizgiyle
            birleştirilmez.
          </p>
        </section>
        <section className="card">
          <p className="eyebrow">SANAL OTURUMUN SON DURUMU</p>
          <h2>
            {state.connection === 'connected' ? 'Bağlı' : 'Bağlantı kesik'} ·{' '}
            {state.freshness === 'fresh'
              ? 'Taze'
              : state.freshness === 'stale'
                ? 'Eski veri'
                : 'Veri yok'}
          </h2>
          <dl className="spec-list">
            <div>
              <dt>Gözlem saati</dt>
              <dd>{date(experiment.as_of)}</dd>
            </div>
            <div>
              <dt>Son ölçüm</dt>
              <dd>{state.last_measurement_at ? date(state.last_measurement_at) : '—'}</dd>
            </div>
            <div>
              <dt>Bekleyen ölçüm</dt>
              <dd>{state.pending}</dd>
            </div>
            <div>
              <dt>Tazelik sınırı</dt>
              <dd>{experiment.config.stale_after_s} sn</dd>
            </div>
            <div>
              <dt>Profil / tohum</dt>
              <dd>
                {recipe.generation.conditions.workload} / {recipe.generation.seed}
              </dd>
            </div>
          </dl>
          <p className="hint">
            Tazelik bu deneyin sanal saatinde hesaplandı. Sayfayı bugün açmak kaydı canlı veri
            yapmaz.
          </p>
          <details>
            <summary>Tekrar üretim bilgileri</summary>
            <p className="mono stream-hash">{experiment.trace_sha256}</p>
            <pre className="stream-recipe">{JSON.stringify(recipe, null, 2)}</pre>
          </details>
        </section>
      </div>
      <section className="card">
        <div className="section-heading">
          <div>
            <h2>Aktarım izi</h2>
            <p className="muted">
              Ölçüm zamanı ile geliş zamanı ayrı tutulur. Düşen ölçümün saati yalnızca simülasyonda
              bilinir.
            </p>
          </div>
          <label className="stream-filter">
            <input
              type="checkbox"
              checked={exceptions}
              onChange={(e) => {
                setExceptions(e.target.checked);
                setOffset(0);
              }}
            />
            Kabul dışındaki olaylar
          </label>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Olay</th>
                <th>Sanal geliş / olay saati</th>
                <th>Ölçüm</th>
                <th>Gecikme</th>
                <th>Sonuç / gerekçe</th>
                <th>Bağlantı / tazelik</th>
              </tr>
            </thead>
            <tbody>
              {page.map((event) => (
                <tr key={event.sequence}>
                  <td className="mono">#{event.sequence}</td>
                  <td>{date(event.at)}</td>
                  <td>
                    {event.sample_id ?? '—'}
                    {event.measurement_at && <small>{date(event.measurement_at)}</small>}
                  </td>
                  <td>
                    {event.measurement_at && event.outcome !== 'dropped'
                      ? `${number((Date.parse(event.at) - Date.parse(event.measurement_at)) / 1000, 3)} sn`
                      : '—'}
                  </td>
                  <td>
                    <span
                      className={`badge ${event.outcome === 'rejected' || event.outcome === 'dropped' ? 'warn' : 'neutral'}`}
                    >
                      {outcomes[event.outcome]}
                    </span>
                    {event.reason && <small>{reasons[event.reason]}</small>}
                  </td>
                  <td>
                    {event.state.connection === 'connected' ? 'Bağlı' : 'Kesik'}
                    <small>
                      {event.state.freshness === 'fresh'
                        ? 'Taze'
                        : event.state.freshness === 'stale'
                          ? 'Eski'
                          : 'Boş'}{' '}
                      · {event.state.pending} bekliyor
                    </small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pager name="Aktarım izi" count={page.length} offset={offset} onChange={setOffset} />
      </section>
    </>
  );
}
