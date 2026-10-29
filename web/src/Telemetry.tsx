import { useEffect, useId, useRef, useState } from 'react';
import type { Sample } from './api/types';
import { date, number } from './labels';
import { Empty } from './components';

type Metric =
  | 'inlet_c'
  | 'reference_inlet_c'
  | 'it_load_kw'
  | 'cooling_kw'
  | 'fan_command_pct'
  | 'fan_feedback_pct';
const chartKinds = {
  temperature: {
    fields: ['inlet_c', 'reference_inlet_c'],
    title: 'Sıcaklık seyri',
    names: ['Giriş', 'Referans'],
    unit: '°C',
    accessible: 'Sentetik giriş ve referans sıcaklığı',
  },
  power: {
    fields: ['it_load_kw', 'cooling_kw'],
    title: 'Yük ve soğutma',
    names: ['IT yükü', 'Soğutma'],
    unit: 'kW',
    accessible: 'Sentetik IT yükü ve soğutma gücü',
  },
  fan: {
    fields: ['fan_command_pct', 'fan_feedback_pct'],
    title: 'Fan tepkisi',
    names: ['Komut', 'Geri bildirim'],
    unit: '%',
    accessible: 'Sentetik fan komutu ve geri bildirimi',
  },
} as const;
export type ChartPoint = { x: number; y: number };

/** Preserve missing observations and communication gaps; use real elapsed time. */
export function seriesSegments(samples: Sample[], field: Metric, interval = 1): ChartPoint[][] {
  const first = samples[0];
  if (!first) return [];
  const start = Date.parse(first.timestamp);
  const segments: ChartPoint[][] = [];
  let segment: ChartPoint[] = [];
  let previous: number | undefined;
  for (const sample of samples) {
    const timestamp = Date.parse(sample.timestamp);
    const value = sample[field];
    if (
      value == null ||
      !Number.isFinite(value) ||
      !Number.isFinite(timestamp) ||
      (previous !== undefined && (timestamp - previous > interval * 1500 || timestamp <= previous))
    ) {
      if (segment.length) segments.push(segment);
      segment = [];
    }
    if (value != null && Number.isFinite(value) && Number.isFinite(timestamp))
      segment.push({ x: (timestamp - start) / 1000, y: value });
    previous = timestamp;
  }
  if (segment.length) segments.push(segment);
  return segments;
}

export function TelemetryChart({
  samples,
  interval = 1,
  kind = 'temperature',
}: {
  kind?: keyof typeof chartKinds;
  samples: Sample[];
  interval?: number;
}) {
  const id = useId();
  const config = chartKinds[kind];
  const container = useRef<HTMLElement>(null);
  const [width, setWidth] = useState(740);
  useEffect(() => {
    const resize = () => {
      const measured = container.current?.getBoundingClientRect().width;
      if (measured) setWidth(Math.max(240, measured));
    };
    resize();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(resize);
    if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, [samples]);
  const inlet = seriesSegments(samples, config.fields[0], interval);
  const reference = seriesSegments(samples, config.fields[1], interval);
  const points = [...inlet.flat(), ...reference.flat()];
  if (!points.length)
    return (
      <Empty>
        {kind === 'temperature'
          ? 'Gösterilebilecek sıcaklık ölçümü yok.'
          : `${config.title}: gösterilebilecek ölçüm yok.`}
      </Empty>
    );
  const min = Math.floor(Math.min(...points.map((point) => point.y)) - 1);
  const max = Math.ceil(Math.max(...points.map((point) => point.y)) + 1);
  const duration = Math.max(1, ...points.map((point) => point.x));
  const x = (value: number) => 48 + (value / duration) * (width - 78);
  const y = (value: number) => 220 - ((value - min) / (max - min)) * 180;
  return (
    <figure className={`chart chart-${kind}`} ref={container}>
      <div className="section-heading">
        <h3>{config.title}</h3>
        <div className="legend">
          <span className="inlet">{config.names[0]}</span>
          <span className="reference">{config.names[1]}</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${width} 265`} role="img" aria-labelledby={`${id}-title ${id}-desc`}>
        <title id={`${id}-title`}>{config.accessible}</title>
        <desc id={`${id}-desc`}>
          Yatay eksen gerçek geçen saniye, dikey eksen {config.unit}. Eksik değerlerde ve zaman
          boşluklarında çizgi kesilir. Tüm ölçümler olay ayrıntısındaki telemetri tablosunda
          bulunur.
        </desc>
        {[0, 1, 2, 3, 4].map((index) => {
          const value = min + ((max - min) * index) / 4;
          return (
            <g key={index}>
              <line className="grid-line" x1="48" x2={width - 30} y1={y(value)} y2={y(value)} />
              <text x="38" y={y(value) + 4} textAnchor="end">
                {number(value, 1)}
              </text>
            </g>
          );
        })}
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <text key={fraction} x={x(duration * fraction)} y="244" textAnchor="middle">
            {number(duration * fraction, 0)} sn
          </text>
        ))}
        <text x="15" y="22">
          {config.unit}
        </text>
        {(
          [
            ['inlet', inlet],
            ['reference', reference],
          ] as const
        ).map(([name, segments]) =>
          segments.map((segment, index) => (
            <g key={`${name}-${index}`} className={`series ${name}`}>
              {segment.length > 1 ? (
                <path
                  d={segment
                    .map(
                      (point, pointIndex) =>
                        `${pointIndex ? 'L' : 'M'}${x(point.x).toFixed(2)} ${y(point.y).toFixed(2)}`,
                    )
                    .join(' ')}
                />
              ) : (
                segment[0] && <circle cx={x(segment[0].x)} cy={y(segment[0].y)} r="3" />
              )}
            </g>
          )),
        )}
      </svg>
      <figcaption>
        Kayıtlı pencere · {config.unit} · Eksik ölçümler ve zaman boşlukları birleştirilmez.
      </figcaption>
    </figure>
  );
}

export function TemperatureChart(props: { samples: Sample[]; interval?: number }) {
  return <TelemetryChart {...props} kind="temperature" />;
}

export function Telemetry({ samples, interval }: { samples: Sample[]; interval?: number }) {
  return (
    <>
      <div className="telemetry-charts">
        <TemperatureChart samples={samples} interval={interval} />
        <TelemetryChart samples={samples} interval={interval} kind="power" />
        <TelemetryChart samples={samples} interval={interval} kind="fan" />
      </div>
      <h3>Ölçüm tablosu</h3>
      <p className="muted">{samples.length} örnek · “—” eksik gözlem anlamına gelir.</p>
      <div
        className="table-scroll sample-table"
        tabIndex={0}
        role="region"
        aria-label="Kaydırılabilir telemetri tablosu"
      >
        <table>
          <thead>
            <tr>
              <th>Zaman</th>
              <th>Giriş °C</th>
              <th>Referans °C</th>
              <th>Dönüş °C</th>
              <th>Üfleme °C</th>
              <th>Ortam °C</th>
              <th>Nem %</th>
              <th>Fan komut %</th>
              <th>Fan geri bildirim %</th>
              <th>Debi m³/sn</th>
              <th>IT yükü kW</th>
              <th>Soğutma kW</th>
            </tr>
          </thead>
          <tbody>
            {samples.map((sample, index) => (
              <tr key={`${sample.sample_id}-${index}`}>
                <td>
                  <time dateTime={sample.timestamp}>{date(sample.timestamp)}</time>
                  <small className="mono">{sample.sample_id}</small>
                </td>
                {(
                  [
                    'inlet_c',
                    'reference_inlet_c',
                    'return_c',
                    'supply_c',
                    'ambient_c',
                    'humidity_pct',
                    'fan_command_pct',
                    'fan_feedback_pct',
                    'airflow_m3s',
                    'it_load_kw',
                    'cooling_kw',
                  ] as const
                ).map((field) => (
                  <td key={field}>{number(sample[field])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
