import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { ApiClient } from './api/client';
import type { Schema } from './api/types';
import type { Session } from './App';
import { Badge, Empty, ErrorNotice, Loading, PageHeading, Pager, Stat } from './components';
import { useLoad } from './hooks';
import { date, groups, scenarios } from './labels';
import { ConditionsForm, ExperimentGuide, defaultConditions } from './Experiment';
import { LatestRunPreview } from './Overview';

export function IncidentList({ api }: { api: ApiClient }) {
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const { data, loading, error } = useLoad(
    () => api.incidents(status, offset),
    [api, status, offset, refresh],
  );
  return (
    <>
      <PageHeading
        kicker="İNCELEME MERKEZİ"
        title="Olay incelemeleri"
        action={
          <a className="button primary" href="#/new">
            + Yeni analiz
          </a>
        }
      >
        Kaydedilen analizleri ve inceleme durumlarını izleyin.
      </PageHeading>
      {data && !loading && error === undefined && (
        <>
          <div className="stats queue-stats">
            <Stat
              title="Görüntülenen kayıt"
              value={data.items.length}
              detail={`Sayfa ${offset / 10 + 1} · Seçili filtre`}
            />
            <Stat
              title="İnceleme bekleyen"
              value={data.items.filter((i) => i.status !== 'closed').length}
              detail="Bu sayfadaki açık ve incelenen olaylar"
            />
            <Stat
              title="Dikkat gerektiren"
              value={
                data.items.filter(
                  (i) =>
                    i.latest_report_status !== 'clear' || i.latest_analysis_status === 'blocked',
                ).length
              }
              detail="Bu sayfadaki son rapor ve engellenen çalışmalar"
            />
          </div>
          {data.items[0] && <LatestRunPreview api={api} runId={data.items[0].latest_run_id} />}
        </>
      )}
      <section className="card">
        <div className="section-heading">
          <div>
            <h2>İnceleme kuyruğu</h2>
            <p className="muted">İnceleme durumu ile analiz sonucu ayrı gösterilir.</p>
          </div>
          <div className="actions">
            <label className="inline-label">
              Durum filtresi
              <select
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value);
                  setOffset(0);
                }}
              >
                <option value="">Tüm durumlar</option>
                <option value="open">Açık</option>
                <option value="investigating">İnceleniyor</option>
                <option value="closed">Kapalı</option>
              </select>
            </label>
            <button
              className="secondary"
              onClick={() => setRefresh((value) => value + 1)}
              disabled={loading}
            >
              Yenile
            </button>
          </div>
        </div>
        {loading ? (
          <Loading />
        ) : error !== undefined ? (
          <ErrorNotice error={error} retry={() => setRefresh((value) => value + 1)} />
        ) : (
          data && (
            <>
              {data.items.length === 0 ? (
                <Empty>
                  Bu sayfada olay yok.{' '}
                  {offset
                    ? 'Önceki sayfaya dönebilirsiniz.'
                    : 'Yeni bir sentetik analiz başlatabilirsiniz.'}
                </Empty>
              ) : (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Olay / ekipman</th>
                        <th>İnceleme</th>
                        <th>Son rapor</th>
                        <th>Çalışma</th>
                        <th>Son güncelleme</th>
                        <th>
                          <span className="sr-only">Ayrıntı</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.items.map((item) => (
                        <tr key={item.incident_id}>
                          <td>
                            <a className="mono strong" href={`#/incidents/${item.incident_id}`}>
                              {item.incident_id}
                            </a>
                            <small>{item.asset_id}</small>
                          </td>
                          <td>
                            <Badge value={item.status} />
                          </td>
                          <td>
                            <Badge
                              value={
                                item.latest_analysis_status === 'blocked'
                                  ? 'blocked'
                                  : item.latest_report_status
                              }
                            />
                          </td>
                          <td>{item.run_count}</td>
                          <td>{date(item.updated_at)}</td>
                          <td>
                            <a className="text-link" href={`#/incidents/${item.incident_id}`}>
                              İncele →
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <Pager
                name="Olaylar"
                offset={offset}
                count={data.items.length}
                onChange={setOffset}
              />
            </>
          )
        )}
      </section>
    </>
  );
}

export function NewAnalysis({ session }: { session: Session }) {
  const [scenario, setScenario] = useState<Schema['ScenarioBody']['scenario']>('fan_loss');
  const [profile, setProfile] = useState<Schema['ScenarioBody']['profile']>('mvp12');
  const [count, setCount] = useState('360');
  const [dynamic, setDynamic] = useState(true);
  const [conditions, setConditions] = useState(defaultConditions);
  const [seed, setSeed] = useState('42');
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const [error, setError] = useState<unknown>();
  const writer = session.principal.role === 'writer';
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (lock.current || !writer) return;
    const sampleCount = Number(count);
    const randomSeed = Number(seed);
    if (
      !count.trim() ||
      !seed.trim() ||
      !Number.isSafeInteger(sampleCount) ||
      sampleCount < 30 ||
      sampleCount > 600 ||
      !Number.isSafeInteger(randomSeed)
    ) {
      setError(new Error('Örnek sayısı 30–600 arasında, tohum ise güvenli bir tam sayı olmalı.'));
      return;
    }
    if (
      dynamic &&
      (!Number.isFinite(conditions.baseline_load_kw) ||
        conditions.baseline_load_kw < 2 ||
        conditions.baseline_load_kw > 8 ||
        !Number.isFinite(conditions.ambient_c) ||
        conditions.ambient_c < 18 ||
        conditions.ambient_c > 40 ||
        !Number.isFinite(conditions.fan_response_s) ||
        conditions.fan_response_s < 1 ||
        conditions.fan_response_s > 20)
    ) {
      setError(new Error('Çalışma koşullarını belirtilen aralıklarda doldurun.'));
      return;
    }
    lock.current = true;
    setBusy(true);
    setError(undefined);
    try {
      const record = await session.api.analyze({
        scenario,
        profile,
        count: sampleCount,
        seed: randomSeed,
        ...(dynamic ? { conditions } : {}),
      });
      if (mounted.current) window.location.hash = `/incidents/${record.result.incident_id}`;
    } catch (issue) {
      if (mounted.current) setError(issue);
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <>
      <PageHeading kicker="SENTETİK TELEMETRİ" title="Yeni analiz">
        Bir senaryo oluşturun; uzmanlar yalnızca ihtiyaç duyulan adımlarda çalışsın.
      </PageHeading>
      {!writer && (
        <p className="notice warn">
          Salt okunur oturum. Analiz başlatmak için yazma yetkisiyle bağlanın.
        </p>
      )}
      <div className="form-layout">
        <section className="card">
          <h2>Analiz yapılandırması</h2>
          <p className="muted">Tek termal bölge · 1 sn örnekleme · Kayıtlı deney</p>
          {error !== undefined && <ErrorNotice error={error} />}
          <form onSubmit={submit}>
            <fieldset disabled={!writer || busy}>
              <label htmlFor="model">Simülasyon modeli</label>
              <select
                id="model"
                value={dynamic ? 'dynamic' : 'reference'}
                onChange={(e) => setDynamic(e.target.value === 'dynamic')}
              >
                <option value="dynamic">Dinamik işletim · Gecikme ve değişken yük</option>
                <option value="reference">Referans · Önceki sabit model</option>
              </select>
              <label htmlFor="scenario">Senaryo</label>
              <select
                id="scenario"
                value={scenario}
                onChange={(event) => setScenario(event.target.value as typeof scenario)}
              >
                {scenarios.map(([id, name]) => (
                  <option value={id} key={id}>
                    {name}
                  </option>
                ))}
              </select>
              <label htmlFor="profile">Uzman profili</label>
              <select
                id="profile"
                value={profile}
                onChange={(event) => setProfile(event.target.value as typeof profile)}
              >
                <option value="mvp12">mvp12 · 12 uygulanmış uzman</option>
                <option value="core6">core6 · İlk 6 uzman</option>
              </select>
              <p className="hint">
                Profildeki tüm uzmanlar her çalışmada çağrılmaz. Yürütülen adımlar rapordaki ajan
                izinde görünür.
              </p>
              <div className="form-row">
                <div>
                  <label htmlFor="count">Örnek sayısı</label>
                  <input
                    id="count"
                    type="number"
                    min="30"
                    max="600"
                    step="1"
                    required
                    value={count}
                    onChange={(event) => setCount(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="seed">Rastgelelik tohumu</label>
                  <input
                    id="seed"
                    type="number"
                    step="1"
                    required
                    value={seed}
                    onChange={(event) => setSeed(event.target.value)}
                  />
                </div>
              </div>
              {dynamic && <ConditionsForm value={conditions} onChange={setConditions} />}
              <button className="primary wide" disabled={!writer || busy}>
                {busy ? 'Analiz çalışıyor ve kaydediliyor…' : 'Analizi başlat ve kaydet'}
              </button>
            </fieldset>
          </form>
        </section>
        <ExperimentGuide
          scenario={scenario}
          count={Number(count)}
          dynamic={dynamic}
          conditions={conditions}
        />
      </div>
    </>
  );
}

export function AgentCatalog({ api }: { api: ApiClient }) {
  const [refresh, setRefresh] = useState(0);
  const { data, loading, error } = useLoad(() => api.agents(), [api, refresh]);
  return (
    <>
      <PageHeading kicker="UZMAN MİMARİSİ" title="Ajan kataloğu">
        Rollerin kapsamı, uygulanma durumu ve izinli araçları.
      </PageHeading>
      {loading ? (
        <Loading />
      ) : error !== undefined ? (
        <ErrorNotice error={error} retry={() => setRefresh((value) => value + 1)} />
      ) : (
        data && (
          <>
            <div className="stats">
              <Stat
                title="Kayıtlı rol"
                value={data.length}
                detail="Altı grup, her grupta altı rol"
              />
              <Stat
                title="Uygulanmış uzman"
                value={data.filter((item) => item.status === 'active').length}
                detail="İhtiyaca göre deterministik yürütme"
              />
              <Stat
                title="Planlı rol"
                value={data.filter((item) => item.status === 'planned').length}
                detail="Henüz uygulama yok"
              />
            </div>
            <div className="notice neutral">
              <b>Global Supervisor çalışıyor.</b> 36 rolün dışında yer alır; araç izinlerini, görev
              bütçelerini ve doğrulama kapılarını yönetir. Grup koordinatörleri planlıdır.
            </div>
            {Object.entries(groups).map(([id, title]) => (
              <section className="agent-group" key={id}>
                <h2>
                  <span>{id}</span>
                  {title}
                </h2>
                <div className="agent-grid">
                  {data
                    .filter((item) => item.group === id)
                    .map((agent) => (
                      <article className={`agent-card ${agent.status}`} key={agent.agent_id}>
                        <div className="section-heading">
                          <span className="mono">{agent.agent_id}</span>
                          <Badge value={agent.status} />
                        </div>
                        <h3>{agent.name}</h3>
                        <p>{agent.purpose}</p>
                        {agent.allowed_tools.length > 0 && (
                          <small className="mono">{agent.allowed_tools.join(', ')}</small>
                        )}
                      </article>
                    ))}
                </div>
              </section>
            ))}
          </>
        )
      )}
    </>
  );
}
