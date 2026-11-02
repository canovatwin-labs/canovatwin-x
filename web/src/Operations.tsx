import { useState } from 'react';
import type { ApiClient } from './api/client';
import { Badge, Empty, ErrorNotice, Loading, PageHeading, Stat } from './components';
import { useLoad } from './hooks';
import { date, groups } from './labels';
import { LatestRunPreview } from './Overview';

export function Operations({ api }: { api: ApiClient }) {
  const [refresh, setRefresh] = useState(0);
  const state = useLoad(async () => {
    const [assets, agents, incidents] = await Promise.all([
      api.assets(),
      api.agents(),
      api.incidents(''),
    ]);
    return { assets, agents, incidents };
  }, [api, refresh]);
  const data = state.data;
  const active = data?.agents.filter((agent) => agent.status === 'active').length ?? 0;
  const open = data?.incidents.items.filter((incident) => incident.status !== 'closed').length ?? 0;
  const closed = (data?.incidents.items.length ?? 0) - open;
  return (
    <div className="operations-page">
      <PageHeading
        kicker="CANOVATWIN / OPERASYON MERKEZİ"
        title="Soğutma operasyonlarına genel bakış"
        action={
          <div className="actions">
            <button
              className="secondary"
              disabled={state.loading}
              onClick={() => setRefresh((value) => value + 1)}
            >
              Görünümü yenile
            </button>
            <a className="button primary" href="#/new">
              Yeni deney başlat ↗
            </a>
          </div>
        }
      >
        Kayıtlı ekipmanlar, ölçümler ve inceleme akışı. Sentetik pilot · Canlı tesis bağlantısı yok.
      </PageHeading>
      {state.loading ? (
        <Loading />
      ) : state.error ? (
        <ErrorNotice error={state.error} retry={() => setRefresh((value) => value + 1)} />
      ) : (
        data && (
          <>
            <div className="ops-kpis">
              <Stat
                title="Görüntülenen ekipman"
                value={data.assets.items.length}
                detail="Katalogdaki ilk 10 ekipman"
              />
              <Stat
                title="Kayıtlı analiz"
                value={data.assets.items.reduce((sum, asset) => sum + asset.run_count, 0)}
                detail="Görüntülenen ekipmanların tüm koşumları"
              />
              <Stat
                title="Açık inceleme"
                value={open}
                detail="Son 10 olayın açık ve incelenen kayıtları"
              />
              <Stat
                title="Uygulanmış uzman"
                value={`${active} / ${data.agents.length}`}
                detail="Kayıtlı rol uygulamaları · canlı çalışma sayısı değil"
              />
            </div>
            <div className="ops-grid">
              <section className="card fleet-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">ASSET EXPLORER</p>
                    <h2>Ekipman filosu</h2>
                  </div>
                  <a href="#/assets">Tüm ekipmanlar ↗</a>
                </div>
                <p className="muted">
                  Her hedef bağımsız tek bölgeli modeldir. Aşağıdaki kartlar fiziksel tesis
                  topolojisi değildir.
                </p>
                {data.assets.items.length ? (
                  <div className="fleet-map">
                    {data.assets.items.map((asset) => (
                      <a
                        className="fleet-unit"
                        key={asset.asset_id}
                        href={`#/assets/${encodeURIComponent(asset.asset_id)}`}
                      >
                        <div className="unit-top">
                          <span
                            className={`status-light ${asset.latest_run_id ? 'recorded' : ''}`}
                          />
                          <span>{asset.latest_run_id ? 'KAYIT VAR' : 'ÖLÇÜM BEKLENİYOR'}</span>
                          <span className="unit-model">SANAL ÜNİTE</span>
                        </div>
                        <div className="rack-visual" aria-hidden="true">
                          {[0, 1, 2, 3].map((i) => (
                            <div key={i}>
                              <i />
                              <i />
                              <span />
                            </div>
                          ))}
                        </div>
                        <h3>{asset.definition?.name ?? asset.asset_id}</h3>
                        <span className="mono">{asset.asset_id}</span>
                        <div className="unit-metrics">
                          <span>
                            <strong>{asset.run_count}</strong> koşum
                          </span>
                          <span>
                            <strong>{asset.open_incident_count}</strong> açık olay
                          </span>
                        </div>
                        <small>
                          {asset.last_recorded_at
                            ? `Son kayıt ${date(asset.last_recorded_at)}`
                            : 'Henüz ölçüm kaydedilmedi'}
                        </small>
                      </a>
                    ))}
                  </div>
                ) : (
                  <Empty>Katalogda ekipman yok. Yeni veri gelene kadar ölçüm gösterilmez.</Empty>
                )}
              </section>
              <section className="card">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">İNCELEME DAĞILIMI</p>
                    <h2>Operasyon kuyruğu</h2>
                  </div>
                  <Badge value="simulation" />
                </div>
                <div className="ops-distribution">
                  <svg
                    viewBox="0 0 180 180"
                    role="img"
                    aria-label={`Son ${data.incidents.items.length} olay: ${open} açık veya inceleniyor, ${closed} kapalı`}
                  >
                    <circle className="ring-track" cx="90" cy="90" r="66" />
                    {data.incidents.items.length > 0 && (
                      <circle
                        className="ring-value"
                        cx="90"
                        cy="90"
                        r="66"
                        pathLength="100"
                        strokeDasharray={`${(open / data.incidents.items.length) * 100} 100`}
                        transform="rotate(-90 90 90)"
                      />
                    )}
                    <text className="ring-count" x="90" y="88" textAnchor="middle">
                      {data.incidents.items.length}
                    </text>
                    <text className="ring-label" x="90" y="111" textAnchor="middle">
                      KAYITLI OLAY
                    </text>
                  </svg>
                  <div className="distribution-key">
                    <p>
                      <span className="key-dot cyan" />
                      Açık / inceleniyor <b>{open}</b>
                    </p>
                    <p>
                      <span className="key-dot slate" />
                      Kapalı <b>{closed}</b>
                    </p>
                    <small>
                      İlk sayfadaki son 10 olay. Arıza olasılığı veya başarı skoru değildir.
                    </small>
                  </div>
                </div>
                <a className="button secondary wide" href="#/incidents">
                  İnceleme kuyruğunu aç →
                </a>
              </section>
            </div>
            {data.incidents.items[0] ? (
              <LatestRunPreview api={api} runId={data.incidents.items[0].latest_run_id} />
            ) : (
              <section className="card ops-empty">
                <p className="eyebrow">DIGITAL TWIN LAB</p>
                <h2>İlk ölçüm penceresiyle başlayın</h2>
                <p className="muted">
                  Grafikler kayıtlı veriden oluşturulur. Bir senaryo çalıştırdığınızda sıcaklık, fan
                  tepkisi ve termal güç burada görünür.
                </p>
                <a className="button primary" href="#/stream">
                  Akış deneyi oluştur ↗
                </a>
              </section>
            )}
            <div className="ops-grid">
              <section className="card">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">UZMAN KATMANLARI</p>
                    <h2>Ajan uygulama haritası</h2>
                  </div>
                  <a href="#/agents">Kataloğu incele ↗</a>
                </div>
                <div className="domain-grid">
                  {Object.entries(groups).map(([group, name]) => {
                    const agents = data.agents.filter((agent) => agent.group === group);
                    const implemented = agents.filter((agent) => agent.status === 'active').length;
                    return (
                      <div key={group} className="domain-cell">
                        <span className="domain-code">{group}</span>
                        <div>
                          <strong>{name}</strong>
                          <div
                            className="domain-meter"
                            role="meter"
                            aria-label={`${name} uygulanmış rol`}
                            aria-valuemin={0}
                            aria-valuemax={agents.length || 1}
                            aria-valuenow={implemented}
                          >
                            <span
                              style={{
                                width: `${agents.length ? (implemented / agents.length) * 100 : 0}%`,
                              }}
                            />
                          </div>
                          <small>
                            {implemented} / {agents.length} uygulanmış
                          </small>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
              <section className="card">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">KAYITLI İNCELEMELER</p>
                    <h2>Son olaylar</h2>
                  </div>
                  <a href="#/incidents">Tümünü aç ↗</a>
                </div>
                {data.incidents.items.length ? (
                  <div className="recent-events">
                    {data.incidents.items.slice(0, 5).map((incident) => (
                      <a key={incident.incident_id} href={`#/incidents/${incident.incident_id}`}>
                        <span>
                          <strong>{incident.asset_id}</strong>
                          <small className="mono">{incident.incident_id}</small>
                        </span>
                        <Badge
                          value={incident.latest_report_status ?? incident.latest_analysis_status}
                        />
                      </a>
                    ))}
                  </div>
                ) : (
                  <Empty>Henüz olay kaydı yok.</Empty>
                )}
              </section>
            </div>
          </>
        )
      )}
    </div>
  );
}
