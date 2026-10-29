import { useRef, useState, type FormEvent } from 'react';
import { ApiError } from './api/client';
import type { Incident, Status } from './api/types';
import type { Session } from './App';
import { Badge, Empty, ErrorNotice, Loading, PageHeading, Pager, Stat } from './components';
import { useLoad } from './hooks';
import { date, label } from './labels';
import { EvidenceView, ReportView, TraceView } from './Report';
import { Telemetry } from './Telemetry';
import { PlantSnapshot } from './Overview';

const transitions: Record<Status, Status[]> = {
  open: ['investigating'],
  investigating: ['open', 'closed'],
  closed: ['open'],
};
const tabs = [
  ['report', 'Rapor'],
  ['telemetry', 'Telemetri'],
  ['evidence', 'Kanıtlar'],
  ['trace', 'Ajan izi'],
  ['history', 'Geçmiş'],
] as const;
type Tab = (typeof tabs)[number][0];

export function IncidentDetail({ session, id }: { session: Session; id: string }) {
  const { api } = session;
  const [refresh, setRefresh] = useState(0);
  const [tab, setTab] = useState<Tab>('report');
  const [selectedRun, setSelectedRun] = useState<string>();
  const [runsOffset, setRunsOffset] = useState(0);
  const [auditOffset, setAuditOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const [error, setError] = useState<unknown>();
  const [notice, setNotice] = useState('');
  const [replayDifferences, setReplayDifferences] = useState<string[]>([]);
  const [statusReason, setStatusReason] = useState('');
  const loaded = useLoad(async () => {
    const [incident, runs, audit, agents] = await Promise.all([
      api.incident(id),
      api.runs(id, runsOffset),
      api.audit(id, auditOffset),
      api.agents(),
    ]);
    const record = await api.run(selectedRun ?? incident.latest_run_id);
    return { incident, runs, audit, agents, record };
  }, [api, id, selectedRun, refresh, runsOffset, auditOffset]);
  async function changeStatus(incident: Incident, target: Status, reason: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(undefined);
    setNotice('');
    setReplayDifferences([]);
    try {
      await api.transition(id, { target, expected_revision: incident.revision, reason });
      setStatusReason('');
      setNotice('İnceleme durumu gerekçesiyle kaydedildi.');
      setRefresh((value) => value + 1);
    } catch (issue) {
      setError(issue);
      if (issue instanceof ApiError && issue.status === 409) setRefresh((value) => value + 1);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function replay(runId: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(undefined);
    setNotice('');
    setReplayDifferences([]);
    try {
      const result = await api.replay(runId);
      setNotice(
        result.matches
          ? 'Yeniden analiz kaydedildi. Süreler dışındaki sonuçlar eşleşiyor.'
          : 'Yeniden analiz kaydedildi. Önceki sonuçtan farklar var; inceleme gerekli.',
      );
      setReplayDifferences(result.differences);
      setSelectedRun(result.record.run_id);
      setRunsOffset(0);
      setAuditOffset(0);
      setRefresh((value) => value + 1);
    } catch (issue) {
      setError(issue);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  const data = loaded.data;
  return (
    <>
      <a className="back-link" href="#/incidents">
        ← Olay incelemeleri
      </a>
      <PageHeading kicker="OLAY AYRINTISI" title="Kanıt ve inceleme">
        Ölçümden rapora uzanan kayıtlı çalışma.
      </PageHeading>
      {notice && (
        <div className="notice neutral" role="status">
          <p>{notice}</p>
          {replayDifferences.length > 0 && (
            <ul>
              {replayDifferences.map((difference, index) => (
                <li key={index}>{difference}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      {error !== undefined && <ErrorNotice error={error} />}
      {loaded.loading ? (
        <Loading />
      ) : loaded.error !== undefined ? (
        <ErrorNotice error={loaded.error} retry={() => setRefresh((value) => value + 1)} />
      ) : (
        data && (
          <>
            <section className="card incident-header">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">{data.incident.asset_id}</p>
                  <p className="mono strong">{id}</p>
                  <small>İlk kayıt: {date(data.incident.created_at)}</small>
                </div>
                <div className="actions">
                  <Badge value={data.incident.status} />
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => setRefresh((value) => value + 1)}
                  >
                    Güncelle
                  </button>
                </div>
              </div>
              <div className="stats">
                <Stat
                  title="İnceleme revizyonu"
                  value={data.incident.revision}
                  detail={`${data.incident.run_count} kaydedilmiş çalışma`}
                />
                <Stat
                  title="Seçili çalışma"
                  value={<Badge value={data.record.result.status} />}
                  detail={`Motor ${data.record.engine_version}`}
                />
                <Stat
                  title="Ajan adımı"
                  value={data.record.result.trace.length}
                  detail={`${data.record.result.trace.filter((step) => step.status === 'completed').length} tamamlanan · ${data.record.result.trace.filter((step) => step.status === 'failed').length} başarısız`}
                />
              </div>
              <div className="run-bar">
                <label className="inline-label">
                  Görüntülenen çalışma
                  <select
                    value={data.record.run_id}
                    onChange={(event) => setSelectedRun(event.target.value)}
                    disabled={busy}
                  >
                    {!data.runs.items.some((run) => run.run_id === data.record.run_id) && (
                      <option value={data.record.run_id}>
                        {date(data.record.recorded_at)} · Seçili çalışma
                      </option>
                    )}
                    {data.runs.items.map((run) => (
                      <option key={run.run_id} value={run.run_id}>
                        {date(run.recorded_at)} · {run.run_id.slice(-8)}
                        {run.replay_of ? ' · Yeniden analiz' : ''}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="secondary"
                  disabled={busy || session.principal.role !== 'writer'}
                  onClick={() => replay(data.record.run_id)}
                >
                  {busy ? 'İşlem sürüyor…' : 'Kaydı yeniden analiz et'}
                </button>
              </div>
              <small className="mono">Çalışma: {data.record.run_id}</small>
              <p className="hint">
                {data.record.request.research ? 'mvp12' : 'core6'} ·{' '}
                {data.record.request.window.samples.length} sentetik ölçüm ·{' '}
                {date(data.record.request.window.samples[0]!.timestamp)} —{' '}
                {date(data.record.request.window.samples.at(-1)!.timestamp)}
              </p>
            </section>
            <section className="card detail-snapshot">
              <PlantSnapshot record={data.record} />
            </section>
            <div className="tabs" role="tablist" aria-label="Analiz ayrıntıları">
              {tabs.map(([key, title], index) => (
                <button
                  key={key}
                  id={`tab-${key}`}
                  role="tab"
                  type="button"
                  aria-selected={tab === key}
                  aria-controls={`view-${key}`}
                  tabIndex={tab === key ? 0 : -1}
                  onClick={() => setTab(key)}
                  onKeyDown={(event) => {
                    const nextIndex =
                      event.key === 'ArrowRight'
                        ? (index + 1) % tabs.length
                        : event.key === 'ArrowLeft'
                          ? (index + tabs.length - 1) % tabs.length
                          : event.key === 'Home'
                            ? 0
                            : event.key === 'End'
                              ? tabs.length - 1
                              : undefined;
                    if (nextIndex !== undefined) {
                      event.preventDefault();
                      const next = tabs[nextIndex]!;
                      setTab(next[0]);
                      document.getElementById(`tab-${next[0]}`)?.focus();
                    }
                  }}
                >
                  {title}
                  {key === 'evidence' && <span>{data.record.result.evidence.length}</span>}
                </button>
              ))}
            </div>
            <section
              className="card tab-panel"
              id={`view-${tab}`}
              role="tabpanel"
              aria-labelledby={`tab-${tab}`}
              tabIndex={0}
            >
              {tab === 'report' && <ReportView record={data.record} />}
              {tab === 'telemetry' && (
                <Telemetry
                  samples={data.record.request.window.samples}
                  interval={data.record.request.research?.expected_interval_s}
                />
              )}
              {tab === 'evidence' && <EvidenceView record={data.record} />}
              {tab === 'trace' && <TraceView record={data.record} agents={data.agents} />}
              {tab === 'history' && (
                <div className="stack">
                  <div>
                    <h3>Çalışma geçmişi</h3>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>Zaman / çalışma</th>
                            <th>İşlem</th>
                            <th>Rapor</th>
                            <th>Görüntüle</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.runs.items.map((run) => (
                            <tr key={run.run_id}>
                              <td>
                                {date(run.recorded_at)}
                                <small className="mono">{run.run_id}</small>
                                {run.replay_of && <small>Kaynak çalışma: {run.replay_of}</small>}
                              </td>
                              <td>
                                <Badge value={run.status} />
                              </td>
                              <td>
                                <Badge value={run.report_status} />
                              </td>
                              <td>
                                <button
                                  className="secondary"
                                  onClick={() => {
                                    setSelectedRun(run.run_id);
                                    setTab('report');
                                  }}
                                >
                                  Aç
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <Pager
                      name="Çalışmalar"
                      offset={runsOffset}
                      count={data.runs.items.length}
                      onChange={setRunsOffset}
                    />
                  </div>
                  <div>
                    <h3>Denetim geçmişi</h3>
                    {data.audit.items.length ? (
                      <ol className="audit-list">
                        {data.audit.items.map((event) => (
                          <li key={event.event_id}>
                            <b>{label(event.action)}</b>
                            <small>
                              {date(event.recorded_at)} · {event.actor} · Revizyon {event.revision}
                            </small>
                            <p>{event.reason}</p>
                            {event.new_status && (
                              <p>
                                {label(event.old_status)} → {label(event.new_status)}
                              </p>
                            )}
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <Empty>Bu sayfada denetim kaydı yok.</Empty>
                    )}
                    <Pager
                      name="Denetim"
                      offset={auditOffset}
                      count={data.audit.items.length}
                      onChange={setAuditOffset}
                    />
                  </div>
                </div>
              )}
            </section>
            <section className="card lifecycle">
              <h2>İnceleme durumunu güncelleyin</h2>
              <p className="muted">
                Bu işlem analiz sonucunu değiştirmez. Değişiklik gerekçesi denetim geçmişine
                eklenir.
              </p>
              {session.principal.role === 'writer' ? (
                <StatusForm
                  incident={data.incident}
                  busy={busy}
                  onSubmit={changeStatus}
                  reason={statusReason}
                  onReasonChange={setStatusReason}
                />
              ) : (
                <p className="notice neutral">
                  Salt okunur oturum. Durum değişikliği ve yeniden analiz için yazma yetkisi
                  gerekir.
                </p>
              )}
            </section>
          </>
        )
      )}
    </>
  );
}

export function StatusForm({
  incident,
  busy,
  onSubmit,
  reason,
  onReasonChange,
}: {
  incident: Incident;
  busy: boolean;
  reason: string;
  onReasonChange: (reason: string) => void;
  onSubmit: (incident: Incident, target: Status, reason: string) => Promise<void>;
}) {
  const options = transitions[incident.status];
  const [chosen, setChosen] = useState<Status>(options[0]!);
  const target = options.includes(chosen) ? chosen : options[0]!;
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!busy && reason.trim()) void onSubmit(incident, target, reason.trim());
  }
  return (
    <form className="status-form" onSubmit={submit}>
      <fieldset disabled={busy}>
        <div className="form-row">
          <div>
            <label htmlFor="target-status">Yeni durum</label>
            <select
              id="target-status"
              value={target}
              onChange={(event) => setChosen(event.target.value as Status)}
            >
              {options.map((value) => (
                <option value={value} key={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="status-reason">İnceleme gerekçesi</label>
            <textarea
              id="status-reason"
              required
              maxLength={2000}
              rows={2}
              value={reason}
              onChange={(event) => onReasonChange(event.target.value)}
            />
          </div>
        </div>
        <button className="primary" disabled={busy || !reason.trim()}>
          {busy ? 'Kaydediliyor…' : 'Durumu kaydet'}
        </button>
        <small>Beklenen revizyon: {incident.revision}</small>
      </fieldset>
    </form>
  );
}
