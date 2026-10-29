import type { RecordAnalysis, Agent } from './api/types';
import { Badge, Empty, Stat } from './components';
import { label, number } from './labels';

export function ReportView({ record }: { record: RecordAnalysis }) {
  const result = record.result;
  const report = result.report;
  const research = report?.research;
  if (!report)
    return (
      <div className="notice danger" role="alert">
        <h2>Çalışma engellendi</h2>
        <p>Nihai rapor oluşturulmadı. Ajan izi ve hata nedenini inceleyin.</p>
        <p>
          <b>{result.failure?.code}</b> · {result.failure?.message}
        </p>
      </div>
    );
  return (
    <div className="stack">
      <div className={`report-summary ${report.status}`}>
        <div className="section-heading">
          <h2>Analiz sonucu</h2>
          <Badge value={report.status} />
        </div>
        <p>{report.summary}</p>
        <small>
          {report.human_review_required
            ? 'İnsan incelemesi gerekli.'
            : 'Tanımlı kurallarla anormallik belirtisi bulunmadı.'}{' '}
          Bu sonuç kesin fiziksel teşhis değildir.
        </small>
      </div>
      <section>
        <h3>Gözlemler</h3>
        {report.observations.length ? (
          <ul className="findings">
            {report.observations.map((observation) => (
              <li key={observation.code}>
                <span className="mono">{observation.code}</span>
                <p>{observation.message}</p>
                <small>Kanıt: {observation.evidence_ids.join(', ')}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Bu çalışmada raporlanan anormallik gözlemi yok.</p>
        )}
      </section>
      <section>
        <h3>Neden adayları</h3>
        {report.hypotheses.length ? (
          <div className="hypotheses">
            {report.hypotheses.map((hypothesis) => (
              <article key={hypothesis.fault_code}>
                <div className="section-heading">
                  <h4>{label(hypothesis.fault_code)}</h4>
                  <Badge value={hypothesis.assessment} />
                </div>
                <p>{hypothesis.explanation}</p>
                <small>Destek: {hypothesis.supporting_evidence.join(', ')}</small>
                <small>Karşı kanıt: {hypothesis.contradicting_evidence?.join(', ') || 'Yok'}</small>
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">
            Nihai raporda neden adayı yok. Veri yetersizse bu, arıza olmadığı anlamına gelmez.
          </p>
        )}
      </section>
      {research && (
        <>
          {research.hypothesis_reviews && research.hypothesis_reviews.length > 0 && (
            <section>
              <h3>Hipotez eleştirisi</h3>
              {research.hypothesis_reviews.map((review) => (
                <article className="review" key={review.fault_code}>
                  <b>{label(review.fault_code)}</b> <Badge value={review.verdict} />
                  <p>{review.reason}</p>
                </article>
              ))}
            </section>
          )}
          {research.model_mae_c != null && (
            <section>
              <h3>Model değerlendirmesi</h3>
              <div className="stats">
                <Stat
                  title="MAE"
                  value={`${number(research.model_mae_c, 4)} °C`}
                  detail="Ortalama mutlak hata"
                />
                <Stat
                  title="RMSE"
                  value={`${number(research.model_rmse_c, 4)} °C`}
                  detail="Kök ortalama kare hata"
                />
                <Stat
                  title="Model yeterliliği"
                  value={research.model_adequate ? 'Uygun' : 'Sınırlı'}
                  detail="Sentetik referansa göre"
                />
              </div>
              <p className="hint">
                Bu değerler sentetik model tutarlılığıdır; gerçek tesis doğruluğunu göstermez.
              </p>
            </section>
          )}
          {research.simulation_cases && research.simulation_cases.length > 0 && (
            <section>
              <h3>What-if hesapları</h3>
              <p className="muted">
                Varsayımsal, açık çevrim hesapları. Fiziksel ekipmana uygulanmaz.
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Senaryo</th>
                      <th>Son sıcaklık</th>
                      <th>Temele göre azalma</th>
                    </tr>
                  </thead>
                  <tbody>
                    {research.simulation_cases.map((item) => (
                      <tr key={item.scenario_id}>
                        <td>{item.scenario_id}</td>
                        <td>{number(item.final_c)} °C</td>
                        <td>{number(item.reduction_vs_baseline_c)} °C</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {research.missing_fields && research.missing_fields.length > 0 && (
            <section>
              <h3>Eksik veri analizi</h3>
              <ul>
                {research.missing_fields.map((field) => (
                  <li key={field.sensor}>
                    {field.sensor}: {field.missing_count} eksik ölçüm · en uzun boşluk{' '}
                    {number(field.longest_missing_s)} sn
                  </li>
                ))}
              </ul>
            </section>
          )}
          {research.document_hits && research.document_hits.length > 0 && (
            <section>
              <h3>Doküman kaynakları</h3>
              <p className="muted">Sözcük tabanlı arama · Kaydedilmiş sürüm</p>
              {research.document_hits.map((hit, index) => (
                <article className="source" key={`${hit.document_id}-${index}`}>
                  <h4>
                    {hit.title} <small>v{hit.version}</small>
                  </h4>
                  <blockquote>{hit.excerpt}</blockquote>
                  <small>
                    {hit.document_id} · karakter {hit.start}–{hit.end}
                  </small>
                  <small className="mono">SHA-256: {hit.content_hash}</small>
                </article>
              ))}
            </section>
          )}
          {research.historical_matches && research.historical_matches.length > 0 && (
            <section>
              <h3>Geçmiş eşleşmeleri</h3>
              <p className="muted">Belirti benzerliği, doğrulanmış teşhis değildir.</p>
              {research.historical_matches.map((match) => (
                <article className="review" key={match.run_id}>
                  <span className="mono">{match.run_id}</span>
                  <p>
                    Belirti benzerliği: {number(match.score * 100, 0)}% · Geçmiş adaylar:{' '}
                    {match.candidate_faults.map(label).join(', ') || 'Yok'}
                  </p>
                  <small>Geçmişteki değerlendirme doğrulanmamıştır.</small>
                </article>
              ))}
            </section>
          )}
        </>
      )}
      <section className="limitations">
        <h3>Sınırlar ve inceleme notları</h3>
        <ul>
          {report.limitations.map((limitation, index) => (
            <li key={index}>{limitation}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export function EvidenceView({ record }: { record: RecordAnalysis }) {
  return (
    <>
      <h3>Kanıt kayıtları</h3>
      <p className="muted">Değerler, üretici ajan ve kaynak ölçüm kimlikleriyle saklanır.</p>
      {record.result.evidence.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Kanıt / metrik</th>
                <th>Değer</th>
                <th>Üretici</th>
                <th>Kaynak</th>
                <th>Ölçümler</th>
              </tr>
            </thead>
            <tbody>
              {record.result.evidence.map((evidence) => (
                <tr key={evidence.evidence_id}>
                  <td>
                    <b className="mono">{evidence.evidence_id}</b>
                    <small>{evidence.metric}</small>
                  </td>
                  <td>
                    {number(evidence.value, 4)} {evidence.unit}
                  </td>
                  <td>{evidence.producer}</td>
                  <td>{label(evidence.source)}</td>
                  <td>
                    <details>
                      <summary>{evidence.sample_ids.length} kimlik</summary>
                      <p className="mono id-list">{evidence.sample_ids.join(', ')}</p>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty>Kaydedilmiş kanıt yok.</Empty>
      )}
    </>
  );
}

export function TraceView({ record, agents }: { record: RecordAnalysis; agents: Agent[] }) {
  const result = record.result;
  return (
    <>
      <h3>Bu çalışmanın ajan izi</h3>
      <p className="muted">
        {result.trace.length} adım kaydı ·{' '}
        {result.trace.filter((step) => step.status === 'completed').length} tamamlanan ·{' '}
        {result.trace.filter((step) => step.status === 'failed').length} başarısız ·{' '}
        {result.total_tool_calls} araç çağrısı · {result.llm_calls} LLM çağrısı ·{' '}
        {result.commands.length} fiziksel komut
      </p>
      <ol className="trace">
        {result.trace.map((step, index) => (
          <li key={`${step.task_id}-${index}`}>
            <span className="trace-number">{index + 1}</span>
            <div>
              <div className="section-heading">
                <h4>
                  <span className="mono">{step.agent_id}</span>{' '}
                  {agents.find((agent) => agent.agent_id === step.agent_id)?.name}
                </h4>
                <Badge value={step.status} />
              </div>
              <p>
                {step.tool_calls} araç çağrısı · {number(step.elapsed_ms, 3)} ms
              </p>
              {step.error_code && <p className="error-text">{step.error_code}</p>}
              <details>
                <summary>Uzman çıktısını göster</summary>
                <pre>
                  {JSON.stringify(
                    result.outputs.find((output) => output.task_id === step.task_id)?.payload ?? {
                      error: step.error_code ?? 'Çıktı yok',
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
            </div>
          </li>
        ))}
      </ol>
    </>
  );
}
