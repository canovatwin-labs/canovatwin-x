import { useId, useState } from 'react';
import type { ApiClient } from './api/client';
import type { RecordAnalysis } from './api/types';
import { Empty, ErrorNotice, Loading } from './components';
import { useLoad } from './hooks';
import { seriesSegments } from './Telemetry';
import { number } from './labels';

export function ComparisonCurves({
  api,
  baseline,
  candidate,
}: {
  api: ApiClient;
  baseline: string;
  candidate: string;
}) {
  const [retry, setRetry] = useState(0);
  const state = useLoad(async () => {
    const [left, right] = await Promise.all([api.run(baseline), api.run(candidate)]);
    if (
      left.run_id !== baseline ||
      right.run_id !== candidate ||
      left.request.window.asset_id !== right.request.window.asset_id
    )
      throw new Error('Grafik kayıt kimlikleri seçilen karşılaştırmayla eşleşmiyor.');
    return { left, right };
  }, [api, baseline, candidate, retry]);
  return state.loading ? (
    <Loading />
  ) : state.error ? (
    <ErrorNotice error={state.error} retry={() => setRetry((v) => v + 1)} />
  ) : state.data ? (
    <CurveChart left={state.data.left} right={state.data.right} />
  ) : null;
}

export function CurveChart({ left, right }: { left: RecordAnalysis; right: RecordAnalysis }) {
  const id = useId();
  const [field, setField] = useState<'inlet_c' | 'it_load_kw' | 'cooling_kw' | 'fan_feedback_pct'>(
    'inlet_c',
  );
  const metrics = {
    inlet_c: ['Giriş sıcaklığı', '°C'],
    it_load_kw: ['IT yükü', 'kW'],
    cooling_kw: ['Termal soğutma gücü', 'kW'],
    fan_feedback_pct: ['Fan geri bildirimi', '%'],
  } as const;
  const [name, unit] = metrics[field];
  const segments = [left, right].map((record) =>
    seriesSegments(
      record.request.window.samples,
      field,
      record.request.research?.expected_interval_s ?? 1,
    ),
  );
  const points = segments.flat(2);
  const values = points.map((point) => point.y);
  const minimum = points.length ? Math.min(...values) : 0;
  const maximum = points.length ? Math.max(...values) : 1;
  const padding = Math.max(1, (maximum - minimum) * 0.05, Math.abs(maximum) * 0.01);
  const low = minimum - padding,
    high = maximum + padding;
  if (!Number.isFinite(high - low) || high <= low)
    return <Empty>Ölçümler desteklenen grafik sayısal aralığını aşıyor.</Empty>;
  const duration = Math.max(1, ...points.map((p) => p.x));
  const x = (value: number) => 50 + (value / duration) * 700;
  const y = (value: number) => 220 - ((value - low) / (high - low)) * 180;
  return (
    <section className="card asset-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">KAYITLI EĞRİLER</p>
          <h2>İki koşum, ortak ölçek</h2>
        </div>
        <label className="inline-label">
          Grafik kanalı
          <select value={field} onChange={(event) => setField(event.target.value as typeof field)}>
            {Object.entries(metrics).map(([key, [label]]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="notice warn">
        Her koşumun ilk kaydedilmiş ölçümü 0 sn kabul edilir. Bu, duvar saati veya arıza başlangıcı
        hizalaması değildir. Eksik ölçümler ve zaman boşlukları birleştirilmez; yeniden örnekleme
        yapılmaz.
      </p>
      <p className="muted mono">
        Temel: {left.run_id}
        <br />
        Aday: {right.run_id}
      </p>
      {points.length ? (
        <figure className="chart comparison-curve">
          <div className="legend">
            <span>Temel · düz çizgi</span>
            <span className="reference">Aday · kesikli çizgi</span>
          </div>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Kaydırılabilir karşılaştırmalı eğri"
          >
            <svg viewBox="0 0 800 265" role="img" aria-labelledby={`${id}-title ${id}-description`}>
              <title id={`${id}-title`}>{name} koşum karşılaştırması</title>
              <desc id={`${id}-description`}>
                Yatay eksen her koşumun ilk ölçümünden geçen saniye; dikey eksen {unit}. Ortak
                ölçek; interpolasyon ve arıza başlangıcı hizalaması yok.
              </desc>
              {[0, 1, 2, 3, 4].map((i) => (
                <g key={i}>
                  <line
                    className="grid-line"
                    x1={50}
                    x2={750}
                    y1={y(low + ((high - low) * i) / 4)}
                    y2={y(low + ((high - low) * i) / 4)}
                  />
                  <text x={42} y={y(low + ((high - low) * i) / 4) + 4} textAnchor="end">
                    {number(low + ((high - low) * i) / 4, 1)}
                  </text>
                  <text x={x((duration * i) / 4)} y={247} textAnchor="middle">
                    {number((duration * i) / 4, 0)} sn
                  </text>
                </g>
              ))}
              {segments.map((series, side) =>
                series.map((segment, i) => (
                  <g key={`${side}-${i}`} className={`series ${side ? 'reference' : 'inlet'}`}>
                    {segment.length > 1 ? (
                      <path
                        d={segment.map((p, j) => `${j ? 'L' : 'M'}${x(p.x)} ${y(p.y)}`).join(' ')}
                      />
                    ) : (
                      <circle cx={x(segment[0]!.x)} cy={y(segment[0]!.y)} r={3} />
                    )}
                  </g>
                )),
              )}
            </svg>
          </div>
          <figcaption>
            {unit} · Her çizgi yalnızca kendi kayıtlı ölçümlerini gösterir. İstatistiksel veya
            nedensel iyileşme puanı değildir.
          </figcaption>
        </figure>
      ) : (
        <Empty>Bu kanalda iki koşumda da gösterilebilir ölçüm yok.</Empty>
      )}
    </section>
  );
}
