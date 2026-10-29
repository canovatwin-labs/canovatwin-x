import type { Schema } from './api/types';
import { scenarios } from './labels';

type Conditions = Schema['OperatingConditions'];
export const workloadNames = { steady: 'Sabit yük', cyclic: 'Dalgalı yük', batch: 'Toplu işlem' };
export const defaultConditions: Conditions = {
  workload: 'cyclic',
  baseline_load_kw: 4.2,
  ambient_c: 30,
  fan_response_s: 6,
};
const descriptions: Record<Schema['ScenarioBody']['scenario'], string> = {
  normal: 'Arıza eklenmez. İş yükü ve ortam değişirken kontrolün verdiği tepki incelenir.',
  fan_loss: 'Fan performansı düşer; komut ile geri bildirim ayrışır ve hava debisi azalır.',
  sensor_bias:
    'Giriş sensörü referans ölçümden +5 °C sapar. Fiziksel sıcaklık aynı hatayı taşımaz.',
  sensor_missing: 'Giriş sensörünün verisi kesilir. Eksik ölçümler sıfırla doldurulmaz.',
  load_surge: 'IT yüküne 4,2 kW eklenir. Isıl atalet ve kontrolün toparlanması gözlenir.',
  cooling_loss: 'Soğutma etkinliği azalır. Fan çalışırken ısı uzaklaştırma gücü düşer.',
  airflow_restriction: 'Hava yolundaki kısıt nedeniyle aynı fan hızında daha düşük debi oluşur.',
  fan_mismatch:
    'Fan geri bildirimi %20 düzeyine yönelir; kontrol komutu bunu izlemek zorunda değildir.',
  communication_loss: 'Tüm telemetri akışı kesilir; analiz saati ilerlemeye devam eder.',
  control_oscillation:
    'Fan komutu 10 saniyelik çevrimlerle salınır. Ekipman gecikmesi tepkiyi sönümler.',
  combined: 'Fan kaybı ve soğutma kaybı birlikte gelişir; birden fazla aday neden incelenir.',
};

export function ConditionsForm({
  value,
  onChange,
}: {
  value: Conditions;
  onChange: (value: Conditions) => void;
}) {
  return (
    <div className="conditions-panel">
      <h3>Çalışma koşulları</h3>
      <label htmlFor="workload">İş yükü profili</label>
      <select
        id="workload"
        value={value.workload}
        onChange={(e) => onChange({ ...value, workload: e.target.value as Conditions['workload'] })}
      >
        {Object.entries(workloadNames).map(([key, name]) => (
          <option key={key} value={key}>
            {name}
          </option>
        ))}
      </select>
      <div className="form-row">
        {(
          [
            ['baseline_load_kw', 'Temel IT yükü (kW)', 2, 8, 0.1],
            ['ambient_c', 'Ortam sıcaklığı (°C)', 18, 40, 0.5],
            ['fan_response_s', 'Fan zaman sabiti (sn)', 1, 20, 1],
          ] as const
        ).map(([key, title, min, max, step]) => (
          <div key={key}>
            <label htmlFor={key}>{title}</label>
            <input
              id={key}
              type="number"
              required
              min={min}
              max={max}
              step={step}
              value={Number.isFinite(value[key]) ? value[key] : ''}
              onChange={(e) =>
                onChange({ ...value, [key]: e.target.value === '' ? NaN : Number(e.target.value) })
              }
            />
            <small className="muted">
              {min}–{max} {key === 'fan_response_s' ? 'sn · %63 tepki süresi' : ''}
            </small>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ExperimentGuide({
  scenario,
  count,
  dynamic,
  conditions,
}: {
  scenario: Schema['ScenarioBody']['scenario'];
  count: number;
  dynamic: boolean;
  conditions: Conditions;
}) {
  const valid = Number.isInteger(count) && count >= 30 && count <= 600;
  return (
    <aside className="experiment-guide stack">
      <article className="card experiment-card">
        <div className="section-heading">
          <span className="eyebrow">DENEY BRİFİNGİ</span>
          <span className="badge neutral">Sentetik</span>
        </div>
        <h2>{scenarios.find(([id]) => id === scenario)?.[1]}</h2>
        <p>{descriptions[scenario]}</p>
        <div className="experiment-timeline" aria-label="Planlanan deney evreleri">
          <div>
            <b>01</b>
            <span>Başlangıç</span>
            <small>0 sn</small>
          </div>
          <div>
            <b>02</b>
            <span>{scenario === 'normal' ? 'İşletim' : 'Arıza başlangıcı'}</span>
            <small>{valid ? Math.floor(count / 3) : '—'} sn</small>
          </div>
          <div>
            <b>03</b>
            <span>Son ölçüm</span>
            <small>{valid ? count - 1 : '—'} sn</small>
          </div>
        </div>
        <p className="hint">
          Planlanan zaman çizelgesi; sonuç tahmini değildir. İletişim kaybında kayıt akışı ikinci
          evrede durur.
        </p>
      </article>
      <article className="card">
        <p className="eyebrow">MODELİN İÇİNDE</p>
        <dl className="spec-list">
          <div>
            <dt>Isıl bölge</dt>
            <dd>1 · 120 kJ/K</dd>
          </div>
          <div>
            <dt>Nominal soğutma</dt>
            <dd>10 kW</dd>
          </div>
          <div>
            <dt>Nominal hava debisi</dt>
            <dd>2,5 m³/sn</dd>
          </div>
          <div>
            <dt>İş yükü</dt>
            <dd>{dynamic ? workloadNames[conditions.workload] : 'Sabit referans'}</dd>
          </div>
          <div>
            <dt>Fan tepkisi</dt>
            <dd>
              {dynamic
                ? `${Number.isFinite(conditions.fan_response_s) ? conditions.fan_response_s : '—'} sn zaman sabiti`
                : 'Anlık'}
            </dd>
          </div>
          <div>
            <dt>Soğutma tepkisi</dt>
            <dd>{dynamic ? '10 sn zaman sabiti' : 'Anlık'}</dd>
          </div>
        </dl>
        <p className="hint">
          {dynamic
            ? 'Dalgalı yük: 90/23 sn çevrimler. Toplu işlem: 120 sn çevrimde 45 sn tam yük artışı. Ortam ±1,5 °C yavaş değişir; sensör gecikmesi 2 sn.'
            : 'Önceki deneylerle karşılaştırma için özgün üretici.'}
        </p>
        <p className="model-limit">
          Tek bölge enerji dengesi kullanılır. Nem temsili bir sinyaldir. Saha kalibrasyonu ve
          kabinler arası hava akışı henüz yoktur.
        </p>
      </article>
    </aside>
  );
}
