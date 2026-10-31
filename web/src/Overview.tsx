import type { ApiClient } from './api/client';
import type { RecordAnalysis } from './api/types';
import { Badge, ErrorNotice, Loading } from './components';
import { useLoad } from './hooks';
import { date, number, scenarios } from './labels';
import { TelemetryChart } from './Telemetry';
import { workloadNames } from './Experiment';

export function PlantSnapshot({ record }: { record: RecordAnalysis }) {
  const samples = record.request.window.samples;
  const last = samples.at(-1)!;
  const age = Math.max(0, (Date.parse(record.request.as_of) - Date.parse(last.timestamp)) / 1000);
  const generation = record.generation ?? record.stream_experiment?.recipe.generation;
  return (
    <>
      <div className="snapshot-heading">
        <div>
          <span className="eyebrow">SANAL TESİS / TEK ISIL BÖLGE</span>
          <p>Son kaydedilen ölçüm · {date(last.timestamp)}</p>
        </div>
        <span className="badge neutral">Canlı bağlantı yok</span>
      </div>
      {age > 1.5 && (
        <p className="notice warn">
          Son ölçüm, analiz saatinin {number(age, 0)} sn gerisinde. Ekran eski ölçümü gösteriyor.
        </p>
      )}
      <div className="plant-flow" aria-label="Son ölçüme dayalı şematik hava ve ısı akışı">
        <article className="plant-node cooling-node">
          <span className="node-id">01 / SOĞUTMA ÜNİTESİ</span>
          <strong>
            {number(last.cooling_kw)} <small>kW</small>
          </strong>
          <p>Üfleme {number(last.supply_c)} °C</p>
          <small>Fan geri bildirimi %{number(last.fan_feedback_pct, 1)}</small>
        </article>
        <div className="flow-connector">
          <b>→</b>
          <span>{number(last.airflow_m3s)} m³/sn</span>
        </div>
        <article className="plant-node rack-node">
          <span className="node-id">02 / IT ISI YÜKÜ</span>
          <strong>
            {number(last.it_load_kw)} <small>kW</small>
          </strong>
          <p>Giriş {number(last.inlet_c)} °C</p>
          <small>Referans {number(last.reference_inlet_c)} °C</small>
        </article>
        <div className="flow-connector warm">
          <b>→</b>
          <span>Isınan hava</span>
        </div>
        <article className="plant-node return-node">
          <span className="node-id">03 / DÖNÜŞ HATTI</span>
          <strong>
            {number(last.return_c)} <small>°C</small>
          </strong>
          <p>Ortam {number(last.ambient_c)} °C</p>
          <small>Bağıl nem %{number(last.humidity_pct, 1)}</small>
        </article>
      </div>
      <div className="snapshot-meta">
        <span>{samples.length} kayıtlı örnek · 1 sanal ekipman</span>
        {generation ? (
          <span>
            {workloadNames[generation.conditions.workload]} · Tohum {generation.seed} ·{' '}
            {generation.generator_version}
          </span>
        ) : (
          <span>Üretim ayarları bu kayıtta bulunmuyor</span>
        )}
      </div>
      {generation && (
        <details className="experiment-details">
          <summary>Kayıtlı deney koşulları</summary>
          <dl className="spec-list">
            <div>
              <dt>Planlanan senaryo</dt>
              <dd>{scenarios.find(([id]) => id === generation.scenario)?.[1]}</dd>
            </div>
            <div>
              <dt>Planlanan örnek</dt>
              <dd>{generation.count}</dd>
            </div>
            <div>
              <dt>Temel IT yükü</dt>
              <dd>{number(generation.conditions.baseline_load_kw)} kW</dd>
            </div>
            <div>
              <dt>Temel ortam sıcaklığı</dt>
              <dd>{number(generation.conditions.ambient_c)} °C</dd>
            </div>
            <div>
              <dt>Fan zaman sabiti</dt>
              <dd>{number(generation.conditions.fan_response_s)} sn</dd>
            </div>
            <div>
              <dt>Üretim başlangıcı</dt>
              <dd>{date(generation.start)}</dd>
            </div>
          </dl>
          <p className="hint">
            Ayarlar deney metadatasıdır. Ajanlar analizde saklanan ölçümleri kullanır.
          </p>
        </details>
      )}
    </>
  );
}

export function LatestRunPreview({ api, runId }: { api: ApiClient; runId: string }) {
  const loaded = useLoad(() => api.run(runId), [api, runId]);
  return (
    <section className="card operations-overview">
      <div className="section-heading">
        <div>
          <p className="eyebrow">OPERASYON GÖRÜNÜMÜ</p>
          <h2>Kaydedilmiş tesis görünümü</h2>
          <small className="muted">Sayfadaki ilk olayın son çalışması</small>
        </div>
        {loaded.data && (
          <a className="button secondary" href={`#/incidents/${loaded.data.result.incident_id}`}>
            Analiz ayrıntıları →
          </a>
        )}
      </div>
      {loaded.loading ? (
        <Loading />
      ) : loaded.error !== undefined ? (
        <ErrorNotice error={loaded.error} />
      ) : (
        loaded.data && (
          <>
            <PlantSnapshot record={loaded.data} />
            <div className="overview-charts">
              <TelemetryChart
                samples={loaded.data.request.window.samples}
                interval={loaded.data.request.research?.expected_interval_s}
              />
              <TelemetryChart
                samples={loaded.data.request.window.samples}
                interval={loaded.data.request.research?.expected_interval_s}
                kind="power"
              />
            </div>
            <div className="result-ribbon">
              <Badge
                value={
                  loaded.data.result.status === 'blocked'
                    ? 'blocked'
                    : loaded.data.result.report?.status
                }
              />
              <p>
                {loaded.data.result.report?.summary ??
                  'Doğrulama kapısı çalışmayı engelledi; nihai rapor yok.'}
              </p>
              <span>{loaded.data.result.trace.length} ajan adımı</span>
            </div>
          </>
        )
      )}
    </section>
  );
}
