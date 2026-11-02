import { useRef, useState, type FormEvent } from 'react';
import type { ApiClient } from './api/client';
import type { Schema } from './api/types';
import { Badge, Empty, ErrorNotice, Loading, PageHeading } from './components';
import { useLoad } from './hooks';
import { date, number } from './labels';

const identifier = /^[A-Za-z0-9_-]{1,100}$/;
export function comparisonLink(baseline: string, candidate?: string) {
  return `#/compare?${new URLSearchParams({ baseline, ...(candidate ? { candidate } : {}) })}`;
}

export function Comparison({
  api,
  initialBaseline = '',
  initialCandidate = '',
}: {
  api: ApiClient;
  initialBaseline?: string;
  initialCandidate?: string;
}) {
  const baselineInput = useRef<HTMLInputElement>(null);
  const candidateInput = useRef<HTMLInputElement>(null);
  const [baseline, setBaseline] = useState(initialBaseline);
  const [candidate, setCandidate] = useState(initialCandidate);
  const [selection, setSelection] = useState<[string, string] | undefined>(() =>
    identifier.test(initialBaseline) &&
    identifier.test(initialCandidate) &&
    initialBaseline !== initialCandidate
      ? [initialBaseline, initialCandidate]
      : undefined,
  );
  const [error, setError] = useState<unknown>();
  const [invalidField, setInvalidField] = useState<'baseline' | 'candidate'>();
  const [retry, setRetry] = useState(0);
  const state = useLoad(
    () => (selection ? api.compare(selection[0], selection[1]) : Promise.resolve(null)),
    [api, selection, retry],
  );
  function submit(event: FormEvent) {
    event.preventDefault();
    const left = baseline.trim(),
      right = candidate.trim();
    if (!identifier.test(left) || !identifier.test(right) || left === right) {
      const field = !identifier.test(left) ? 'baseline' : 'candidate';
      setInvalidField(field);
      (field === 'baseline' ? baselineInput : candidateInput).current?.focus();
      setError(new Error('Aynı ekipmana ait iki farklı ve geçerli çalışma kimliği seçin.'));
      return;
    }
    setError(undefined);
    setInvalidField(undefined);
    setSelection([left, right]);
  }
  function edit(value: string, side: 'baseline' | 'candidate') {
    (side === 'baseline' ? setBaseline : setCandidate)(value);
    setSelection(undefined);
    setError(undefined);
    setInvalidField(undefined);
  }
  return (
    <>
      <PageHeading kicker="KAYITLI DENEYLER" title="Koşum karşılaştırması">
        Aynı ekipmanın iki kaydını inceleyin. Farklar aday − temel yönündedir; iyileşme puanı
        değildir.
      </PageHeading>
      <section className="card">
        <h2>Karşılaştırılacak kayıtlar</h2>
        <p id="comparison-help" className="muted">
          Olayın Çalışmalar bölümünden iki kayıt seçebilir veya çalışma kimliklerini buraya
          yazabilirsiniz. Karşılaştırma yeni analiz oluşturmaz.
        </p>
        <form
          className="comparison-form"
          onSubmit={submit}
          noValidate
          aria-describedby="comparison-help"
        >
          <label htmlFor="comparison-baseline">Temel çalışma kimliği</label>
          <input
            ref={baselineInput}
            id="comparison-baseline"
            aria-invalid={invalidField === 'baseline' || undefined}
            aria-describedby={invalidField === 'baseline' ? 'comparison-error' : undefined}
            value={baseline}
            maxLength={100}
            onChange={(e) => edit(e.target.value, 'baseline')}
            autoComplete="off"
            spellCheck={false}
          />
          <label htmlFor="comparison-candidate">Aday çalışma kimliği</label>
          <input
            ref={candidateInput}
            id="comparison-candidate"
            aria-invalid={invalidField === 'candidate' || undefined}
            aria-describedby={invalidField === 'candidate' ? 'comparison-error' : undefined}
            value={candidate}
            maxLength={100}
            onChange={(e) => edit(e.target.value, 'candidate')}
            autoComplete="off"
            spellCheck={false}
          />
          {error !== undefined && (
            <div id="comparison-error">
              <ErrorNotice error={error} />
            </div>
          )}
          <button className="primary" disabled={!!selection && state.loading}>
            Kayıtları karşılaştır
          </button>
        </form>
      </section>
      {!selection ? (
        <Empty>İki kayıt seçildiğinde ölçüm farkları burada görünür.</Empty>
      ) : state.loading ? (
        <Loading />
      ) : state.error ? (
        <ErrorNotice error={state.error} retry={() => setRetry((v) => v + 1)} />
      ) : state.data ? (
        <ComparisonResult result={state.data} />
      ) : null}
    </>
  );
}

function ComparisonResult({ result }: { result: Schema['RunComparison'] }) {
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }),
    );
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `comparison-${result.baseline.run_id}-${result.candidate.run_id}.json`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return (
    <section className="card comparison-result" aria-label="Karşılaştırma sonucu">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{result.asset_id}</p>
          <h2>Ölçüm ve aktarım farkları</h2>
        </div>
        <div className="actions">
          <span className="badge neutral">{result.comparison_version}</span>
          <button className="secondary" onClick={download}>
            Karşılaştırmayı JSON indir
          </button>
        </div>
      </div>
      <p className="notice warn">
        Betimleyici sonuç: daha düşük veya yüksek değer tek başına iyileşme, nedensellik ya da
        elektrik tasarrufu göstermez. Ortalamalar zaman ağırlıklı değildir; eksik okumalar
        doldurulmaz.
      </p>
      {!result.same_measurement_timestamps && (
        <p className="notice warn" role="status">
          Ölçüm zamanları eşleşmiyor. Pencereler noktasal olarak hizalanmadı.
        </p>
      )}
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Koşum özeti">
        <table>
          <caption>Değişmez kayıtların özeti</caption>
          <thead>
            <tr>
              <th scope="col">Özellik</th>
              <th scope="col">Temel</th>
              <th scope="col">Aday</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Kayıt ve rapor</th>
              {[result.baseline, result.candidate].map((run) => (
                <td key={run.run_id}>
                  <span className="mono">{run.run_id}</span>
                  <br />
                  <a href={`#/incidents/${encodeURIComponent(run.incident_id)}`}>Olayı aç</a>
                  <br />
                  <Badge value={run.report_status ?? run.analysis_status} />
                </td>
              ))}
            </tr>
            <tr>
              <th scope="row">Ölçüm aralığı</th>
              {[result.baseline, result.candidate].map((run) => (
                <td key={run.run_id}>
                  {date(run.window_start)}
                  <br />
                  {date(run.window_end)}
                </td>
              ))}
            </tr>
            <tr>
              <th scope="row">Motor / kaynak</th>
              <td>
                {result.baseline.engine_version} / {result.baseline.source}
              </td>
              <td>
                {result.candidate.engine_version} / {result.candidate.source}
              </td>
            </tr>
            <tr>
              <th scope="row">Örnek sayısı</th>
              <td>{result.baseline.sample_count}</td>
              <td>{result.candidate.sample_count}</td>
            </tr>
            <tr>
              <th scope="row">Aktarım: kabul / ret / kayıp</th>
              {[result.baseline, result.candidate].map((run) => (
                <td key={run.run_id}>
                  {number(run.transport_accepted, 0)} / {number(run.transport_rejected, 0)} /{' '}
                  {number(run.transport_dropped, 0)}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <h3>Kanal istatistikleri</h3>
      <p className="muted">
        Her hücre: ortalama · son okuma · eksik / toplam. — değeri mevcut olmayan okumayı gösterir.
      </p>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Kanal farkları">
        <table>
          <caption>Fark yönü: aday − temel</caption>
          <thead>
            <tr>
              <th scope="col">Kanal / birim</th>
              <th scope="col">Temel</th>
              <th scope="col">Aday</th>
              <th scope="col">Ortalama farkı</th>
              <th scope="col">Son okuma farkı</th>
            </tr>
          </thead>
          <tbody>
            {result.channels.map((channel) => (
              <tr key={channel.field}>
                <th scope="row">
                  {channel.name}
                  <br />
                  {channel.unit}
                </th>
                {[channel.baseline, channel.candidate].map((stats, i) => (
                  <td key={i}>
                    {number(stats.mean)} · {number(stats.final)} · {stats.missing_count} /{' '}
                    {stats.valid_count + stats.missing_count}
                    <small>
                      Min: {number(stats.minimum)} · Maks: {number(stats.maximum)}
                    </small>
                  </td>
                ))}
                <td>
                  {number(channel.mean_delta)} {channel.unit}
                </td>
                <td>
                  {number(channel.final_delta)} {channel.unit}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3>Değişen girdiler</h3>
      {result.differing_inputs.length ? (
        <ul>
          {result.differing_inputs.map((path) => (
            <li key={path}>
              <code>{path}</code>
            </li>
          ))}
        </ul>
      ) : (
        <p>Kaydedilmiş girdi bağlamları aynı. Bu, saha doğrulaması anlamına gelmez.</p>
      )}
      <details>
        <summary>Sözleşmenin sınırlamaları</summary>
        <ul>
          {result.limitations.map((text) => (
            <li key={text}>{text}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}
