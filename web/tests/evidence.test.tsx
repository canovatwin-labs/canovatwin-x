import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { EvidenceView, TraceView, evidenceReferences } from '../src/EvidenceExplorer';
import { IncidentDetail } from '../src/IncidentDetail';
import { data, session } from './fixtures';

function fixture() {
  const record = structuredClone(data.record);
  const first = record.result.evidence[0]!;
  record.result.evidence = Array.from({ length: 12 }, (_, i) => ({
    ...first,
    evidence_id: `evidence-${i}`,
    metric: `metric-${i}`,
    producer: i === 11 ? ('A03' as const) : ('A02' as const),
  }));
  record.result.report!.evidence_ids = ['evidence-0'];
  record.result.report!.observations = [
    { code: 'OBS', message: 'Stored finding', evidence_ids: ['evidence-0'] },
  ];
  record.result.report!.hypotheses = [
    {
      fault_code: 'FAULT_F01',
      assessment: 'candidate',
      explanation: 'Stored hypothesis',
      supporting_evidence: ['evidence-0'],
      contradicting_evidence: ['evidence-1'],
    },
  ];
  return record;
}

describe('recorded evidence investigation', () => {
  it('separates explicit report, observation, support and counter-evidence references', () => {
    const record = fixture();
    expect(evidenceReferences(record, 'evidence-0').map((ref) => ref.kind)).toEqual([
      'Rapor kaynağı',
      'Gözlem',
      'Destek',
    ]);
    expect(evidenceReferences(record, 'evidence-1')).toEqual([
      { kind: 'Karşı kanıt', text: 'Fan performans kaybı' },
    ]);
    expect(evidenceReferences(record, 'evidence-2')).toEqual([]);
    record.result.report = null;
    expect(evidenceReferences(record, 'evidence-0')).toEqual([]);
  });
  it('pages, filters by exact producer, clears selection and supports keyboard activation', async () => {
    const user = userEvent.setup();
    render(<EvidenceView record={fixture()} />);
    const catalog = within(screen.getByRole('region', { name: 'Kanıt seçimi' }));
    await user.click(
      within(catalog.getByRole('navigation')).getByRole('button', { name: 'Sonraki' }),
    );
    expect(catalog.queryByRole('button', { name: /evidence-0 / })).toBeNull();
    const choice = catalog.getByRole('button', { name: /evidence-11 / });
    choice.focus();
    await user.keyboard('{Enter}');
    expect(choice).toHaveAttribute('aria-pressed', 'true');
    await user.selectOptions(screen.getByLabelText('Üretici ajan'), 'A03');
    expect(screen.getByRole('status')).toHaveTextContent('1 eşleşen / 12 kayıt');
    expect(screen.getByText(/görmek için bir kanıt seçin/)).toBeVisible();
    expect(catalog.getByRole('button', { name: 'Önceki' })).toBeDisabled();
    await user.type(screen.getByLabelText('Kanıt veya metrik ara'), 'not-in-record');
    expect(screen.getByText('Filtreye uyan kanıt yok.')).toBeVisible();
  });
  it('keeps missing source readings missing and pages actual sample references', async () => {
    const record = fixture();
    record.result.evidence[0]!.sample_ids = [
      ...record.request.window.samples.slice(0, 11).map((s) => s.sample_id),
      'absent',
    ];
    record.request.window.samples[0]!.inlet_c = null;
    render(<EvidenceView record={record} initialId="evidence-0" />);
    const table = within(screen.getByRole('region', { name: 'Kaynak ölçüm tablosu' }));
    expect(table.getAllByRole('row')).toHaveLength(11);
    expect(within(table.getAllByRole('row')[1]!).getAllByRole('cell')[1]).toHaveTextContent('—');
    expect(screen.getByText(/11 \/ 12 referans/)).toBeVisible();
    await userEvent.click(
      within(screen.getByRole('navigation', { name: 'Kaynak ölçümleri sayfalama' })).getByRole(
        'button',
        { name: 'Sonraki' },
      ),
    );
    expect(table.getByText('Pencerede bulunamadı')).toBeVisible();
    expect(table.getAllByRole('row')).toHaveLength(3);
  });
  it('does not invent a report for blocked runs or select a nonexistent evidence ID', () => {
    const record = fixture();
    record.result.report = null;
    const { rerender } = render(<EvidenceView key="one" record={record} initialId="evidence-0" />);
    expect(screen.getByText(/Çalışmanın nihai raporu yok/)).toBeVisible();
    rerender(<EvidenceView key="two" record={record} initialId="missing" />);
    expect(screen.getByText('İstenen kanıt bu çalışmada bulunamadı.')).toBeVisible();
  });
  it('renders stored markup as text and handles an empty archive', () => {
    const record = fixture();
    record.result.evidence[0]!.metric = '<img src=x onerror=alert(1)>';
    const { container, rerender } = render(<EvidenceView record={record} initialId="evidence-0" />);
    expect(screen.getAllByText('<img src=x onerror=alert(1)>')).toHaveLength(2);
    expect(container.querySelector('img')).toBeNull();
    record.result.evidence = [];
    rerender(<EvidenceView record={record} />);
    expect(screen.getByText('Kaydedilmiş kanıt yok.')).toBeVisible();
  });
  it('matches outputs by both task and agent and exposes failed steps without a fabricated output', async () => {
    const record = structuredClone(data.blocked);
    const failed = record.result.trace.find((s) => s.status === 'failed')!;
    // A matching task name from a different agent is not this step's output.
    record.result.outputs[0]!.task_id = failed.task_id;
    render(<TraceView record={record} agents={[]} initialAgent={failed.agent_id} />);
    expect(screen.getByRole('alert')).toHaveTextContent(failed.error_code!);
    await userEvent.click(screen.getByText('Uzman çıktısını göster'));
    expect(screen.getByText('Bu ajan ve görev kimliğiyle eşleşen çıktı yok.')).toBeVisible();
  });
  it('keeps zero-duration steps finite and distinguishes producer links from task dependencies', async () => {
    const record = fixture();
    record.result.trace.forEach((s) => {
      s.elapsed_ms = 0;
    });
    const onInspectEvidence = vi.fn();
    const { container } = render(
      <TraceView
        record={record}
        agents={data.agents}
        initialAgent="A02"
        onInspectEvidence={onInspectEvidence}
      />,
    );
    expect(container.innerHTML).not.toMatch(/NaN|Infinity/);
    expect(screen.getByText(/belirli bir görev çağrısına atfedilmez/)).toBeVisible();
    await userEvent.click(screen.getByRole('button', { name: /evidence-0 / }));
    expect(onInspectEvidence).toHaveBeenCalledExactlyOnceWith('evidence-0');
  });
  it('does not silently choose a reading when a source identity is duplicated', () => {
    const record = fixture();
    const sample = record.request.window.samples[0]!;
    record.result.evidence[0]!.sample_ids = [sample.sample_id];
    record.request.window.samples.push({ ...sample, inlet_c: 99 });
    render(<EvidenceView record={record} initialId="evidence-0" />);
    expect(screen.getByText('Kimlik birden çok ölçümle eşleşiyor')).toBeVisible();
    const table = screen.getByRole('region', { name: 'Kaynak ölçüm tablosu' });
    expect(table).not.toHaveTextContent('99');
    expect(within(table).queryByText('Ölçümü aç')).toBeNull();
  });
  it('opens a linked evidence on its own archive page and can move focus to its details', async () => {
    render(<EvidenceView record={fixture()} initialId="evidence-11" />);
    expect(screen.getByRole('button', { name: /evidence-11 / })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    expect(screen.getByText('Sayfa 2 · Bu sayfada 2 kayıt')).toBeVisible();
    await userEvent.click(screen.getByRole('button', { name: 'Seçili kanıt ayrıntılarına geç' }));
    expect(screen.getByRole('region', { name: 'Seçili kanıt ayrıntıları' })).toHaveFocus();
  });
  it('shows empty traces without runtime activity', () => {
    const record = fixture();
    record.result.trace = [];
    render(<TraceView record={record} agents={data.agents} />);
    expect(screen.getByText('Kaydedilmiş ajan adımı yok.')).toBeVisible();
    expect(screen.queryByText('Uzman çıktısını göster')).toBeNull();
  });
  it('navigates report → evidence → producer → evidence without writes, then resets for another run', async () => {
    const record = fixture();
    const next = structuredClone(record);
    next.run_id = 'RUN-other';
    next.result.evidence = [];
    const current = session('reader');
    vi.spyOn(current.api, 'incident').mockResolvedValue({
      ...data.incident,
      latest_run_id: record.run_id,
    });
    vi.spyOn(current.api, 'runs').mockResolvedValue({
      ...data.runs,
      items: [record, next].map((r) => ({ ...data.runs.items[0]!, run_id: r.run_id })),
    });
    vi.spyOn(current.api, 'audit').mockResolvedValue(data.audit);
    vi.spyOn(current.api, 'agents').mockResolvedValue(data.agents);
    vi.spyOn(current.api, 'run').mockImplementation(async (id) =>
      id === next.run_id ? next : record,
    );
    const write = vi.spyOn(current.api, 'transition');
    const replay = vi.spyOn(current.api, 'replay');
    const user = userEvent.setup();
    render(<IncidentDetail session={current} id={data.incident.incident_id} />);
    await screen.findByRole('tab', { name: 'Rapor' });
    await user.click(screen.getAllByRole('button', { name: 'evidence-0' })[0]!);
    expect(screen.getByRole('tab', { name: /Kanıtlar/ })).toHaveFocus();
    await user.click(screen.getByRole('button', { name: 'Üreticinin ajan izini aç' }));
    expect(screen.getByRole('tab', { name: 'Ajan izi' })).toHaveFocus();
    await user.click(screen.getByRole('button', { name: /evidence-0 / }));
    expect(screen.getByRole('region', { name: 'Seçili kanıt ayrıntıları' })).toHaveTextContent(
      'evidence-0',
    );
    await user.selectOptions(screen.getByLabelText('Görüntülenen çalışma'), next.run_id);
    expect(await screen.findByText('Kaydedilmiş kanıt yok.')).toBeVisible();
    expect(screen.queryByText('evidence-0')).toBeNull();
    expect(write).not.toHaveBeenCalled();
    expect(replay).not.toHaveBeenCalled();
  });
});
