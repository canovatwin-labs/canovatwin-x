import { useRef, useState } from 'react';
import type { Agent, RecordAnalysis, Sample, Schema } from './api/types';
import { Badge, Empty, Pager, Stat } from './components';
import { date, label, number } from './labels';

type Evidence = Schema['Evidence'];

/** Only explicit references in the stored final report; never infer causality. */
export function evidenceReferences(record: RecordAnalysis, id: string) {
  const report = record.result.report;
  if (!report) return [];
  return [
    ...(report.evidence_ids.includes(id) ? [{ kind: 'Rapor kaynağı', text: 'Nihai rapor' }] : []),
    ...report.observations
      .filter((item) => item.evidence_ids.includes(id))
      .map((item) => ({ kind: 'Gözlem', text: `${item.code} · ${item.message}` })),
    ...report.hypotheses.flatMap((item) => [
      ...(item.supporting_evidence.includes(id)
        ? [{ kind: 'Destek', text: label(item.fault_code) }]
        : []),
      ...(item.contradicting_evidence?.includes(id)
        ? [{ kind: 'Karşı kanıt', text: label(item.fault_code) }]
        : []),
    ]),
  ];
}

export function EvidenceView({
  record,
  initialId,
  onInspectAgent,
}: {
  record: RecordAnalysis;
  initialId?: string;
  onInspectAgent?: (agentId: string) => void;
}) {
  const detailRef = useRef<HTMLElement>(null);
  const [query, setQuery] = useState('');
  const [producer, setProducer] = useState('');
  const [selectedId, setSelectedId] = useState(initialId);
  const evidence = record.result.evidence;
  const [offset, setOffset] = useState(
    () =>
      Math.floor(
        Math.max(
          0,
          evidence.findIndex((item) => item.evidence_id === initialId),
        ) / 10,
      ) * 10,
  );
  const filtered = evidence.filter(
    (item) =>
      (!producer || item.producer === producer) &&
      `${item.evidence_id} ${item.metric}`
        .toLocaleLowerCase('tr')
        .includes(query.trim().toLocaleLowerCase('tr')),
  );
  const selected = evidence.find((item) => item.evidence_id === selectedId);
  function resetFilter() {
    setOffset(0);
    setSelectedId(undefined);
  }
  return (
    <div className="stack evidence-workspace">
      <div className="section-heading">
        <div>
          <p className="eyebrow">KAYITLI KANIT BAĞLARI</p>
          <h3>Ölçümden rapora</h3>
        </div>
        <Badge value={record.result.status} />
      </div>
      <p className="muted">
        Kaynak → üretici → kanıt → rapor bağlantıları kayıtlı kimliklerden okunur. Bu görünüm
        nedensellik veya ajan görev bağımlılığı iddiası taşımaz.
      </p>
      <div className="stats">
        <Stat title="Kanıt" value={evidence.length} detail="Seçili çalışmadaki kayıtlar" />
        <Stat
          title="Üretici"
          value={new Set(evidence.map((item) => item.producer)).size}
          detail="Kanıt üreten farklı ajanlar"
        />
        <Stat
          title="Raporda bağlı"
          value={
            evidence.filter((item) => evidenceReferences(record, item.evidence_id).length > 0)
              .length
          }
          detail="En az bir açık rapor referansı"
        />
      </div>
      <div className="form-row">
        <label>
          Kanıt veya metrik ara
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              resetFilter();
            }}
          />
        </label>
        <label>
          Üretici ajan
          <select
            value={producer}
            onChange={(event) => {
              setProducer(event.target.value);
              resetFilter();
            }}
          >
            <option value="">Bütün üreticiler</option>
            {[...new Set(evidence.map((item) => item.producer))].sort().map((id) => (
              <option key={id}>{id}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="inspection-layout">
        <section aria-label="Kanıt seçimi" className="inspection-catalog">
          <p className="muted" role="status">
            {filtered.length} eşleşen / {evidence.length} kayıt
          </p>
          {filtered.length ? (
            <div className="evidence-choices">
              {filtered.slice(offset, offset + 10).map((item) => (
                <button
                  className="evidence-choice secondary"
                  key={item.evidence_id}
                  aria-label={`${item.evidence_id} · ${item.metric}`}
                  aria-pressed={selectedId === item.evidence_id}
                  onClick={() => setSelectedId(item.evidence_id)}
                >
                  <span className="mono">{item.evidence_id}</span>
                  <strong>{item.metric}</strong>
                  <span>
                    {number(item.value, 4)} {item.unit}
                  </span>
                  <small>
                    {item.producer} · {label(item.source)}
                  </small>
                </button>
              ))}
            </div>
          ) : (
            <Empty>{evidence.length ? 'Filtreye uyan kanıt yok.' : 'Kaydedilmiş kanıt yok.'}</Empty>
          )}
          {selected && (
            <button
              className="secondary"
              onClick={() => {
                detailRef.current?.focus({ preventScroll: true });
                detailRef.current?.scrollIntoView?.({ block: 'start' });
              }}
            >
              Seçili kanıt ayrıntılarına geç
            </button>
          )}
          <Pager
            name="Kanıtlar"
            offset={offset}
            count={filtered.slice(offset, offset + 10).length}
            onChange={setOffset}
          />
        </section>
        <section
          ref={detailRef}
          tabIndex={-1}
          className="inspection-detail"
          aria-label="Seçili kanıt ayrıntıları"
        >
          {selected ? (
            <EvidenceDetail
              key={selected.evidence_id}
              record={record}
              evidence={selected}
              onInspectAgent={onInspectAgent}
            />
          ) : (
            <Empty>
              {selectedId
                ? 'İstenen kanıt bu çalışmada bulunamadı.'
                : 'Kaynak ölçümlerini ve rapor bağlarını görmek için bir kanıt seçin.'}
            </Empty>
          )}
        </section>
      </div>
    </div>
  );
}

function EvidenceDetail({
  record,
  evidence,
  onInspectAgent,
}: {
  record: RecordAnalysis;
  evidence: Evidence;
  onInspectAgent?: (id: string) => void;
}) {
  const [offset, setOffset] = useState(0);
  const references = evidenceReferences(record, evidence.evidence_id);
  const samples = new Map<string, Sample | null>();
  for (const sample of record.request.window.samples) {
    samples.set(sample.sample_id, samples.has(sample.sample_id) ? null : sample);
  }
  const present = evidence.sample_ids.filter((id) => samples.get(id) != null).length;
  const steps = record.result.trace.filter((step) => step.agent_id === evidence.producer);
  return (
    <div className="stack">
      <div className="evidence-chain" aria-label="Kayıtlı kaynak zinciri">
        <div>
          <small>KAYNAK</small>
          <strong>{label(evidence.source)}</strong>
          <span>{evidence.sample_ids.length} ölçüm referansı</span>
        </div>
        <span aria-hidden="true">→</span>
        <div>
          <small>ÜRETİCİ</small>
          <strong>{evidence.producer}</strong>
          <span>{steps.length} kayıtlı adım</span>
        </div>
        <span aria-hidden="true">→</span>
        <div>
          <small>RAPOR</small>
          <strong>{references.length} açık bağ</strong>
          <span>{record.result.report ? 'Nihai rapor tarandı' : 'Nihai rapor yok'}</span>
        </div>
      </div>
      <header>
        <h3 className="mono">{evidence.evidence_id}</h3>
        <p>{evidence.metric}</p>
        <p className="evidence-value">
          {number(evidence.value, 4)} <small>{evidence.unit}</small>
        </p>
      </header>
      {onInspectAgent && (
        <button
          className="secondary"
          disabled={!steps.length}
          onClick={() => onInspectAgent(evidence.producer)}
        >
          Üreticinin ajan izini aç
        </button>
      )}
      <section>
        <h4>Raporda kullanımı</h4>
        {references.length ? (
          <ul className="reference-list">
            {references.map((ref, index) => (
              <li key={index}>
                <b>{ref.kind}</b>
                <p>{ref.text}</p>
              </li>
            ))}
          </ul>
        ) : (
          <Empty>
            {record.result.report
              ? 'Nihai raporda bu kanıta açık referans yok. Bu, başka uzmanların kullanmadığını göstermez.'
              : 'Çalışmanın nihai raporu yok; rapor bağlantısı kurulmadı.'}
          </Empty>
        )}
      </section>
      <section>
        <h4>Kaynak ölçümleri</h4>
        <p className="muted">
          {present} / {evidence.sample_ids.length} referans bu çalışmanın penceresinde tekil olarak
          bulundu. Ham ölçümler kanıtın hesaplanmış değeriyle aynı şey değildir.
        </p>
        {present !== evidence.sample_ids.length && (
          <p className="notice warn">
            Bazı ölçüm kimlikleri bu pencerede yok veya tekil değil; değer üretilmedi veya başka
            kayıttan tamamlanmadı.
          </p>
        )}
        <div className="table-scroll" role="region" aria-label="Kaynak ölçüm tablosu" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>Ölçüm / zaman</th>
                <th>Giriş °C</th>
                <th>Fan %</th>
                <th>Ham kayıt</th>
              </tr>
            </thead>
            <tbody>
              {evidence.sample_ids.slice(offset, offset + 10).map((id, index) => {
                const sample = samples.get(id);
                return (
                  <tr key={`${id}-${index}`}>
                    <td>
                      <span className="mono">{id}</span>
                      <small>
                        {sample
                          ? date(sample.timestamp)
                          : sample === null
                            ? 'Kimlik birden çok ölçümle eşleşiyor'
                            : 'Pencerede bulunamadı'}
                      </small>
                    </td>
                    <td>{number(sample?.inlet_c)}</td>
                    <td>{number(sample?.fan_feedback_pct)}</td>
                    <td>
                      {sample && (
                        <details>
                          <summary>Ölçümü aç</summary>
                          <pre>{JSON.stringify(sample, null, 2)}</pre>
                        </details>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <Pager
          name="Kaynak ölçümleri"
          offset={offset}
          count={evidence.sample_ids.slice(offset, offset + 10).length}
          onChange={setOffset}
        />
      </section>
      <small className="mono">Çalışma: {record.run_id}</small>
    </div>
  );
}

export function TraceView({
  record,
  agents,
  initialAgent,
  onInspectEvidence,
}: {
  record: RecordAnalysis;
  agents: Agent[];
  initialAgent?: string;
  onInspectEvidence?: (id: string) => void;
}) {
  const result = record.result;
  const first = result.trace.findIndex((step) => step.agent_id === initialAgent);
  const [selectedIndex, setSelectedIndex] = useState(Math.max(0, first));
  const step = result.trace[selectedIndex];
  const output =
    step &&
    result.outputs.find((item) => item.task_id === step.task_id && item.agent_id === step.agent_id);
  const maximum = Math.max(0, ...result.trace.map((item) => item.elapsed_ms));
  const produced = step ? result.evidence.filter((item) => item.producer === step.agent_id) : [];
  return (
    <div className="stack">
      <div>
        <p className="eyebrow">KAYITLI YÜRÜTME</p>
        <h3>Bu çalışmanın ajan izi</h3>
      </div>
      <p className="muted">
        {result.trace.length} adım kaydı ·{' '}
        {result.trace.filter((item) => item.status === 'completed').length} tamamlanan ·{' '}
        {result.trace.filter((item) => item.status === 'failed').length} başarısız ·{' '}
        {result.total_tool_calls} araç çağrısı · {result.llm_calls} LLM çağrısı ·{' '}
        {result.commands.length} fiziksel komut
      </p>
      <p className="hint">
        Sıra, kayıt dizisinin sırasıdır. Çubuklar adım sürelerini en uzun adıma göre gösterir;
        başlangıç zamanı, paralellik veya görev bağımlılığı göstermez.
      </p>
      <div className="inspection-layout trace-workspace">
        <section aria-label="Ajan adımları">
          {result.trace.length ? (
            <ol className="execution-list">
              {result.trace.map((item, index) => (
                <li key={`${item.task_id}-${index}`}>
                  <button
                    className="secondary execution-step"
                    aria-pressed={selectedIndex === index}
                    onClick={() => setSelectedIndex(index)}
                  >
                    <span className="execution-step-heading">
                      <span className="mono">
                        {String(index + 1).padStart(2, '0')} · {item.agent_id}
                      </span>
                      <Badge value={item.status} />
                    </span>
                    <strong>
                      {agents.find((agent) => agent.agent_id === item.agent_id)?.name ??
                        'Katalog adı bulunamadı'}
                    </strong>
                    <span className="duration-track" aria-hidden="true">
                      <span
                        style={{ width: `${maximum ? (item.elapsed_ms / maximum) * 100 : 0}%` }}
                      />
                    </span>
                    <small>
                      {number(item.elapsed_ms, 3)} ms · {item.tool_calls} araç çağrısı
                    </small>
                  </button>
                </li>
              ))}
            </ol>
          ) : (
            <Empty>Kaydedilmiş ajan adımı yok.</Empty>
          )}
        </section>
        <section className="inspection-detail" aria-label="Seçili ajan adımı">
          {step ? (
            <div className="stack">
              <header>
                <div className="section-heading">
                  <h3>
                    {step.agent_id} · Adım {selectedIndex + 1}
                  </h3>
                  <Badge value={step.status} />
                </div>
                <p className="mono">{step.task_id}</p>
                <p>
                  {number(step.elapsed_ms, 3)} ms · {step.tool_calls} araç çağrısı
                </p>
              </header>
              {step.error_code && (
                <p className="notice danger" role="alert">
                  {step.error_code}
                </p>
              )}
              <section>
                <h4>Üreticinin kayıtlı kanıtları</h4>
                <p className="muted">
                  Bağlantı üretici ajan kimliğine aittir; belirli bir görev çağrısına atfedilmez.
                </p>
                {produced.length ? (
                  <div className="evidence-choices">
                    {produced.map((item) =>
                      onInspectEvidence ? (
                        <button
                          className="secondary evidence-choice"
                          key={item.evidence_id}
                          aria-label={`${item.evidence_id} · ${item.metric}`}
                          onClick={() => onInspectEvidence(item.evidence_id)}
                        >
                          <b className="mono">{item.evidence_id}</b>
                          <span>
                            {item.metric} · {number(item.value, 4)} {item.unit}
                          </span>
                        </button>
                      ) : (
                        <p key={item.evidence_id}>
                          {item.evidence_id} · {item.metric}
                        </p>
                      ),
                    )}
                  </div>
                ) : (
                  <Empty>Bu üreticiye ait kayıtlı kanıt yok.</Empty>
                )}
              </section>
              <details key={`${selectedIndex}-${step.task_id}`}>
                <summary>Uzman çıktısını göster</summary>
                {output ? (
                  <pre>{JSON.stringify(output.payload, null, 2)}</pre>
                ) : (
                  <p className="notice warn">Bu ajan ve görev kimliğiyle eşleşen çıktı yok.</p>
                )}
              </details>
              <small className="mono">Çalışma: {record.run_id}</small>
            </div>
          ) : (
            <Empty>İncelenecek adım yok.</Empty>
          )}
        </section>
      </div>
    </div>
  );
}
