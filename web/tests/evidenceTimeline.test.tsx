import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { TelemetryChart, seriesSegments } from '../src/Telemetry';
import { EvidenceView } from '../src/EvidenceExplorer';
import { data } from './fixtures';
import type { Sample } from '../src/api/types';

const sample = data.record.request.window.samples[0]!;
function samples(): Sample[] {
  return [0, 1, 4].map((second) => ({
    ...sample,
    sample_id: `s${second}`,
    timestamp: `2026-01-01T00:00:0${second}Z`,
    inlet_c: 20 + second,
    reference_inlet_c: 20,
  }));
}
describe('evidence timeline', () => {
  it('marks only exact unique references and preserves unselected context and time gaps', () => {
    const rows = samples();
    const { container } = render(
      <TelemetryChart samples={rows} highlightedIds={['s1', 'unknown', 's1']} />,
    );
    expect(container.querySelectorAll('.evidence-marker')).toHaveLength(2);
    expect(container.querySelector('.evidence-marker')).toHaveAttribute('data-sample-id', 's1');
    expect(seriesSegments(rows, 'inlet_c')).toEqual([
      [
        { x: 0, y: 20 },
        { x: 1, y: 21 },
      ],
      [{ x: 4, y: 24 }],
    ]);
  });
  it('does not assign ambiguous IDs or missing channel values to markers', () => {
    const rows = samples();
    rows[1]!.inlet_c = null;
    rows.push({ ...rows[0]! });
    const { container } = render(<TelemetryChart samples={rows} highlightedIds={['s0', 's1']} />);
    expect(container.querySelectorAll('.evidence-marker')).toHaveLength(1);
    expect(container.querySelector('.evidence-marker')).toHaveAttribute('data-sample-id', 's1');
  });
  it('hides evidence marks with their series and supports keyboard sample inspection', async () => {
    const user = userEvent.setup();
    const { container } = render(<TelemetryChart samples={samples()} highlightedIds={['s1']} />);
    await user.click(screen.getByRole('button', { name: 'Giriş' }));
    expect(container.querySelectorAll('.evidence-marker')).toHaveLength(1);
    const slider = screen.getByRole('slider');
    slider.focus();
    fireEvent.change(slider, { target: { value: '1' } });
    expect(slider).toHaveValue('1');
    expect(screen.getByRole('status')).toHaveTextContent('Giriş: 21');
    expect(slider).toHaveFocus();
  });
  it('rejects an invalid time origin instead of producing NaN coordinates', () => {
    const rows = samples();
    rows[0]!.timestamp = 'invalid';
    expect(seriesSegments(rows, 'inlet_c')).toEqual([]);
    render(<TelemetryChart samples={rows} highlightedIds={['s1']} />);
    expect(screen.getByText('Gösterilebilecek sıcaklık ölçümü yok.')).toBeVisible();
  });
  it('changes channels inside evidence detail while keeping the stored source references', async () => {
    const user = userEvent.setup();
    const record = structuredClone(data.record);
    record.request.window.samples = samples();
    const evidence = record.result.evidence[0]!;
    evidence.sample_ids = ['s1'];
    const { container } = render(<EvidenceView record={record} initialId={evidence.evidence_id} />);
    expect(screen.getByRole('region', { name: 'Kanıtın zaman bağlamı' })).toBeVisible();
    await user.selectOptions(screen.getByLabelText('Ölçüm kanalı'), 'fan');
    expect(screen.getByRole('heading', { name: 'Fan tepkisi' })).toBeVisible();
    expect(
      [...container.querySelectorAll('.evidence-marker')].every(
        (node) => node.getAttribute('data-sample-id') === 's1',
      ),
    ).toBe(true);
  });
  it('does not render a timeline when no source reference can be resolved', () => {
    const record = structuredClone(data.record);
    const evidence = record.result.evidence[0]!;
    evidence.sample_ids = ['unavailable'];
    render(<EvidenceView record={record} initialId={evidence.evidence_id} />);
    expect(screen.queryByRole('region', { name: 'Kanıtın zaman bağlamı' })).toBeNull();
    expect(screen.getByText('Pencerede bulunamadı')).toBeVisible();
  });
});
