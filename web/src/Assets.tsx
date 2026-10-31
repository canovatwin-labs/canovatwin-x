import { useEffect, useState } from 'react';
import type { ApiClient } from './api/client';
import type { Schema } from './api/types';
import type { Session } from './App';
import { Badge, Empty, ErrorNotice, Loading, PageHeading, Pager, Stat } from './components';
import { useLoad } from './hooks';
import { date, number } from './labels';
import { TelemetryChart } from './Telemetry';

export function AssetSelector({
  api,
  value,
  onSelect,
  onReady,
  disabled,
}: {
  api: ApiClient;
  value: string;
  onSelect: (asset: Schema['AssetDefinition']) => void;
  onReady: (ready: boolean) => void;
  disabled: boolean;
}) {
  const [refresh, setRefresh] = useState(0);
  const loaded = useLoad(() => api.assets(0, true), [api, refresh]);
  const options =
    loaded.data?.items.flatMap((item) => (item.definition ? [item.definition] : [])) ?? [];
  useEffect(() => {
    const selected = loaded.data?.items.find((item) => item.asset_id === value)?.definition;
    onReady(Boolean(selected) && !loaded.loading && loaded.error === undefined);
    if (selected && !loaded.loading) onSelect(selected);
  }, [loaded.data, loaded.loading, loaded.error, onReady, onSelect]);
  if (loaded.error !== undefined)
    return <ErrorNotice error={loaded.error} retry={() => setRefresh((v) => v + 1)} />;
  if (loaded.loading) return <Loading />;
  if (!options.some((item) => item.asset_id === value))
    return (
      <p className="notice danger" role="alert">
        Seçilen ekipman yapılandırılmış katalogda yok. Varlık kataloğundan bir sentetik ünite seçin.
      </p>
    );
  return (
    <>
      <label htmlFor="selected-asset">Ekipman</label>
      <select
        id="selected-asset"
        disabled={disabled}
        value={value}
        onChange={(event) => {
          const selected = options.find((item) => item.asset_id === event.target.value);
          if (selected) onSelect(selected);
        }}
      >
        {options.map((item) => (
          <option key={item.asset_id} value={item.asset_id}>
            {item.name} · {item.asset_id}
          </option>
        ))}
      </select>
    </>
  );
}

export function AssetList({ api }: { api: ApiClient }) {
  const [offset, setOffset] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const loaded = useLoad(() => api.assets(offset), [api, offset, refresh]);
  return (
    <>
      <PageHeading
        kicker="VARLIK / ÖLÇÜM KATALOĞU"
        title="Ekipmanlar"
        action={
          <button
            className="secondary"
            disabled={loaded.loading}
            onClick={() => setRefresh((v) => v + 1)}
          >
            Yenile
          </button>
        }
      >
        Yapılandırılmış sentetik üniteler ve geçmiş kayıtlarda gözlenen ekipmanlar. Sayaçlar seçilen
        ekipmanın kayıtlarından hesaplanır.
      </PageHeading>
      {loaded.loading ? (
        <Loading />
      ) : loaded.error !== undefined ? (
        <ErrorNotice error={loaded.error} retry={() => setRefresh((v) => v + 1)} />
      ) : (
        loaded.data && (
          <>
            <div className="asset-grid">
              {loaded.data.items.map((item) => (
                <article className="card asset-card" key={item.asset_id}>
                  <div className="section-heading">
                    <span className="eyebrow">
                      {item.definition
                        ? 'YAPILANDIRILMIŞ / SENTETİK'
                        : 'YALNIZCA GEÇMİŞTE GÖZLENDİ'}
                    </span>
                    <span className="badge neutral">
                      {item.run_count ? 'Kayıt var' : 'Henüz ölçüm yok'}
                    </span>
                  </div>
                  <h2>
                    <a href={`#/assets/${encodeURIComponent(item.asset_id)}`}>
                      {item.definition?.name ?? item.asset_id}
                    </a>
                  </h2>
                  <p className="mono muted">{item.asset_id}</p>
                  <p>{item.definition?.location ?? 'Konum ve fiziksel model tanımlanmamış'}</p>
                  <div className="asset-counts">
                    <span>
                      <b>{item.incident_count}</b> olay
                    </span>
                    <span>
                      <b>{item.open_incident_count}</b> açık / incelenen
                    </span>
                    <span>
                      <b>{item.run_count}</b> çalışma
                    </span>
                  </div>
                  <small>
                    Son kayıt: {item.last_recorded_at ? date(item.last_recorded_at) : '—'}
                  </small>
                </article>
              ))}
            </div>
            <Pager
              name="Ekipmanlar"
              offset={offset}
              count={loaded.data.items.length}
              onChange={setOffset}
            />
          </>
        )
      )}
      <p className="notice neutral">
        Her sentetik ünite aynı tek bölgeli modelin bağımsız koşumudur. Üniteler arasında ısıl
        etkileşim veya gerçek PLC bağlantısı kurulmaz. Geçmişte gözlenen bir kimlik, fiziksel
        ekipman kaydı olarak doğrulanmış sayılmaz.
      </p>
    </>
  );
}

export function AssetWorkspace({ session, id }: { session: Session; id: string }) {
  const [offset, setOffset] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const loaded = useLoad(async () => {
    const detail = await session.api.asset(id);
    const [incidents, record] = await Promise.all([
      session.api.assetIncidents(id, offset),
      detail.asset.latest_run_id
        ? session.api.run(detail.asset.latest_run_id)
        : Promise.resolve(undefined),
    ]);
    if (record && record.request.window.asset_id !== id)
      throw new Error('Ekipman ile kayıt uyuşmuyor. İnceleme gerekli.');
    return { detail, incidents, record };
  }, [session.api, id, offset, refresh]);
  const content = loaded.data;
  const asset = content?.detail.asset;
  return (
    <>
      <a className="back-link" href="#/assets">
        ← Ekipmanlar
      </a>
      <PageHeading
        kicker="EKİPMAN İNCELEMESİ"
        title={asset?.definition?.name ?? id}
        action={
          <button
            className="secondary"
            disabled={loaded.loading}
            onClick={() => setRefresh((v) => v + 1)}
          >
            Yenile
          </button>
        }
      >
        Ölçüm sözleşmesi, son kayıtlı pencere ve bu ekipmana ait inceleme geçmişi.
      </PageHeading>
      {loaded.loading ? (
        <Loading />
      ) : loaded.error !== undefined ? (
        <ErrorNotice error={loaded.error} retry={() => setRefresh((v) => v + 1)} />
      ) : (
        content &&
        asset && (
          <>
            <div className="stats">
              <Stat
                title="Olay"
                value={asset.incident_count}
                detail="Yalnızca bu ekipmanın tüm kayıtları"
              />
              <Stat
                title="Açık / incelenen"
                value={asset.open_incident_count}
                detail="Kapatılmamış incelemeler"
              />
              <Stat title="Çalışma" value={asset.run_count} detail="Yeniden analizler dahil" />
            </div>
            <section className="card">
              <div className="section-heading">
                <div>
                  <h2>{asset.asset_id}</h2>
                  <p className="muted">
                    {asset.definition
                      ? `${asset.definition.location} · 1 sn örnekleme · bağımsız sentetik model`
                      : 'Yalnızca geçmişte gözlenmiş kimlik; yapılandırılmış fiziksel model yok.'}
                  </p>
                </div>
                <div className="actions">
                  {asset.definition && (
                    <>
                      <a className="button primary" href={`#/new?asset=${encodeURIComponent(id)}`}>
                        Bu ekipmanda analiz
                      </a>
                      <a
                        className="button secondary"
                        href={`#/stream?asset=${encodeURIComponent(id)}`}
                      >
                        Aktarım deneyi
                      </a>
                    </>
                  )}
                  {content.record && (
                    <a
                      className="button secondary"
                      href={`#/incidents/${content.record.result.incident_id}`}
                    >
                      Son rapor
                    </a>
                  )}
                </div>
              </div>
              {content.record ? (
                <>
                  <p className="notice neutral">
                    Kayıtlı pencere · {date(content.record.recorded_at)}. Canlı ölçüm değildir.
                  </p>
                  <TelemetryChart samples={content.record.request.window.samples} />
                </>
              ) : (
                <Empty>Bu ekipman için henüz kaydedilmiş bir ölçüm penceresi yok.</Empty>
              )}
            </section>
            <section className="card asset-section">
              <h2>Ölçüm sözleşmesi ve son pencere</h2>
              <p className="muted">
                Kanonik birimler. Gösterilen sınırlar örnek veri kalite aralıklarıdır; üretici
                emniyet sınırı değildir. Eksik ölçümler doldurulmaz.
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Ölçüm / etiket</th>
                      <th>Birim</th>
                      <th>Örnek aralık</th>
                      <th>Son değer</th>
                      <th>Pencerede eksik</th>
                    </tr>
                  </thead>
                  <tbody>
                    {content.detail.channels.map((channel) => {
                      const samples = content.record?.request.window.samples;
                      const key = channel.field as keyof NonNullable<typeof samples>[number];
                      const last = samples?.at(-1)?.[key];
                      return (
                        <tr key={channel.field}>
                          <td>
                            {channel.name}
                            <small className="mono">{channel.field}</small>
                          </td>
                          <td>{channel.unit}</td>
                          <td>
                            {channel.illustrative_min}–{channel.illustrative_max}
                          </td>
                          <td>{typeof last === 'number' ? number(last) : '—'}</td>
                          <td>
                            {samples
                              ? `${samples.filter((sample) => sample[key] == null).length} / ${samples.length}`
                              : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="card asset-section">
              <h2>Bu ekipmanın olayları</h2>
              {content.incidents.items.length ? (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Olay</th>
                        <th>İnceleme</th>
                        <th>Son rapor</th>
                        <th>Çalışma</th>
                      </tr>
                    </thead>
                    <tbody>
                      {content.incidents.items.map((incident) => (
                        <tr key={incident.incident_id}>
                          <td>
                            <a className="mono" href={`#/incidents/${incident.incident_id}`}>
                              {incident.incident_id}
                            </a>
                          </td>
                          <td>
                            <Badge value={incident.status} />
                          </td>
                          <td>
                            <Badge value={incident.latest_report_status} />
                          </td>
                          <td>{incident.run_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Empty>Bu sayfada ekipmana ait olay yok.</Empty>
              )}
              <Pager
                name="Ekipman olayları"
                count={content.incidents.items.length}
                offset={offset}
                onChange={setOffset}
              />
            </section>
          </>
        )
      )}
    </>
  );
}
