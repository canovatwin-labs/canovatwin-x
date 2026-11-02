import { useState } from 'react';
import type { ApiClient } from './api/client';
import { Badge, Empty, ErrorNotice, Loading, Pager } from './components';
import { useLoad } from './hooks';
import { date } from './labels';

export function RunPicker({
  api,
  baseline,
  candidate,
  onAssetChange,
  onChoose,
}: {
  api: ApiClient;
  baseline: string;
  candidate: string;
  onAssetChange: () => void;
  onChoose: (side: 'baseline' | 'candidate', id: string) => void;
}) {
  const [asset, setAsset] = useState('');
  const [assetOffset, setAssetOffset] = useState(0);
  const [offset, setOffset] = useState(0);
  const [retry, setRetry] = useState(0);
  const assets = useLoad(() => api.assets(assetOffset), [api, assetOffset, retry]);
  const runs = useLoad(
    () => (asset ? api.assetRuns(asset, offset) : Promise.resolve(null)),
    [api, asset, offset, retry],
  );
  return (
    <section className="card asset-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">DENEY ARŞİVİ</p>
          <h2>Ekipmandan koşum seçin</h2>
        </div>
        <button className="secondary" onClick={() => setRetry((v) => v + 1)}>
          Arşivi yenile
        </button>
      </div>
      <p className="muted">
        Farklı olaylardaki koşumlar ve yeniden analizler birlikte listelenir. Seçimler sayfalar
        arasında korunur; ekipman değişikliği iki seçimi de temizler.
      </p>
      {assets.loading ? (
        <Loading />
      ) : assets.error ? (
        <ErrorNotice error={assets.error} retry={() => setRetry((v) => v + 1)} />
      ) : (
        <>
          <label htmlFor="comparison-asset">Karşılaştırılacak ekipman</label>
          <select
            id="comparison-asset"
            value={asset}
            onChange={(event) => {
              setAsset(event.target.value);
              setOffset(0);
              onAssetChange();
            }}
          >
            <option value="">Ekipman seçin</option>
            {asset && !assets.data?.items.some((item) => item.asset_id === asset) && (
              <option value={asset}>{asset}</option>
            )}
            {assets.data?.items.map((item) => (
              <option key={item.asset_id} value={item.asset_id}>
                {item.definition?.name ?? item.asset_id} · {item.run_count} koşum
              </option>
            ))}
          </select>
          <Pager
            name="Ekipman kataloğu"
            offset={assetOffset}
            count={assets.data?.items.length ?? 0}
            onChange={setAssetOffset}
          />
        </>
      )}
      {!asset ? (
        <Empty>Kayıtlı koşumları görmek için bir ekipman seçin.</Empty>
      ) : runs.loading ? (
        <Loading />
      ) : runs.error ? (
        <ErrorNotice error={runs.error} retry={() => setRetry((v) => v + 1)} />
      ) : (
        runs.data && (
          <>
            {runs.data.items.length ? (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Ekipmanın kayıtlı koşumları"
              >
                <table>
                  <caption>{asset} · En yeni kayıttan eskiye</caption>
                  <thead>
                    <tr>
                      <th>Kayıt / olay</th>
                      <th>Sonuç</th>
                      <th>Seçim</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.data.items.map((run) => (
                      <tr key={run.run_id}>
                        <td>
                          {date(run.recorded_at)}
                          <small className="mono">{run.run_id}</small>
                          <small className="mono">{run.incident_id}</small>
                          {run.replay_of && <small>Yeniden analiz · {run.replay_of}</small>}
                        </td>
                        <td>
                          <Badge value={run.report_status ?? run.status} />
                        </td>
                        <td>
                          <div className="actions">
                            <button
                              className="secondary"
                              aria-pressed={baseline === run.run_id}
                              disabled={candidate === run.run_id}
                              onClick={() => onChoose('baseline', run.run_id)}
                            >
                              Temel seç
                            </button>
                            <button
                              className="secondary"
                              aria-pressed={candidate === run.run_id}
                              disabled={baseline === run.run_id}
                              onClick={() => onChoose('candidate', run.run_id)}
                            >
                              Aday seç
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>
                Bu sayfada koşum yok. Önceki sayfaya dönün veya bu ekipmanda yeni bir deney
                oluşturun.
              </Empty>
            )}
            <Pager
              name="Ekipman koşumları"
              offset={offset}
              count={runs.data.items.length}
              onChange={setOffset}
            />
          </>
        )
      )}
    </section>
  );
}
