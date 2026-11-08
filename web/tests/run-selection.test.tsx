import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { RunPicker } from '../src/RunPicker';
import { ComparisonCurves, CurveChart } from '../src/ComparisonCurves';
import { data, session } from './fixtures';

it('selects runs from the chosen asset and clears selections on asset change', async () => {
  const api = session('reader').api;
  const list = vi.spyOn(api, 'assetRuns').mockResolvedValue(data.runs);
  const choose = vi.fn(),
    change = vi.fn();
  render(<RunPicker api={api} baseline="" candidate="" onChoose={choose} onAssetChange={change} />);
  await userEvent.selectOptions(
    await screen.findByLabelText('Karşılaştırılacak ekipman'),
    'synthetic-unit-01',
  );
  const region = await screen.findByRole('region', { name: 'Ekipmanın kayıtlı koşumları' });
  await userEvent.click(within(region).getAllByRole('button', { name: 'Temel seç' })[0]!);
  expect(choose).toHaveBeenCalledWith('baseline', data.runs.items[0]!.run_id);
  expect(list).toHaveBeenCalledWith('synthetic-unit-01', 0);
  await userEvent.selectOptions(
    screen.getByLabelText('Karşılaştırılacak ekipman'),
    'synthetic-unit-02',
  );
  expect(change).toHaveBeenCalledTimes(2);
});

it('paginates runs before choosing and prevents the same run on both sides', async () => {
  const api = session().api;
  const item = data.runs.items[0]!;
  const list = vi
    .spyOn(api, 'assetRuns')
    .mockResolvedValueOnce({
      ...data.runs,
      items: Array.from({ length: 10 }, (_, i) => ({ ...item, run_id: `RUN-${i}` })),
    })
    .mockResolvedValue({ ...data.runs, items: [] });
  render(
    <RunPicker
      api={api}
      baseline="RUN-0"
      candidate=""
      onChoose={vi.fn()}
      onAssetChange={vi.fn()}
    />,
  );
  await userEvent.selectOptions(
    await screen.findByLabelText('Karşılaştırılacak ekipman'),
    'synthetic-unit-01',
  );
  const region = await screen.findByRole('region', { name: 'Ekipmanın kayıtlı koşumları' });
  expect(within(region).getAllByRole('button', { name: 'Aday seç' })[0]).toBeDisabled();
  await userEvent.click(
    within(screen.getByRole('navigation', { name: 'Ekipman koşumları sayfalama' })).getByRole(
      'button',
      { name: 'Sonraki' },
    ),
  );
  expect(await screen.findByText(/Bu sayfada koşum yok/)).toBeVisible();
  expect(list).toHaveBeenLastCalledWith('synthetic-unit-01', 10);
});

it('renders shared-scale curves with an explicit elapsed-time rule and missing segments', () => {
  const left = structuredClone(data.record),
    right = structuredClone(data.record);
  right.run_id = 'RUN-candidate';
  right.request.window.samples = right.request.window.samples.map((s) => ({ ...s, inlet_c: null }));
  const { container } = render(<CurveChart left={left} right={right} />);
  expect(screen.getByText(/duvar saati veya arıza başlangıcı/)).toBeVisible();
  expect(container.querySelectorAll('.series.reference')).toHaveLength(0);
  expect(container.querySelectorAll('.series.inlet').length).toBeGreaterThan(0);
  fireEvent.change(screen.getByLabelText('Grafik kanalı'), { target: { value: 'cooling_kw' } });
  expect(screen.getByRole('img')).toHaveAccessibleName(/Termal soğutma gücü/);
});

it('rejects mismatched returned run identities before drawing', async () => {
  const api = session().api;
  vi.spyOn(api, 'run').mockResolvedValue(data.record);
  render(<ComparisonCurves api={api} baseline="RUN-a" candidate="RUN-b" />);
  expect(await screen.findByRole('alert')).toHaveTextContent('eşleşmiyor');
  expect(screen.queryByRole('img')).not.toBeInTheDocument();
});

it('uses elapsed origins instead of silently aligning wall clocks', () => {
  const left = structuredClone(data.record),
    right = structuredClone(data.record);
  right.run_id = 'RUN-shifted';
  right.request.window.samples = right.request.window.samples.map((sample) => ({
    ...sample,
    timestamp: new Date(Date.parse(sample.timestamp) + 3600000).toISOString(),
  }));
  const { container } = render(<CurveChart left={left} right={right} />);
  expect(container.querySelector('.series.inlet path')?.getAttribute('d')).toBe(
    container.querySelector('.series.reference path')?.getAttribute('d'),
  );
  expect(screen.getByText(/duvar saati veya arıza başlangıcı/)).toBeVisible();
});

it('never connects an isolated reading across a missing sample', () => {
  const left = structuredClone(data.record),
    right = structuredClone(data.record);
  left.request.window.samples = left.request.window.samples.slice(0, 3);
  left.request.window.samples[1]!.inlet_c = null;
  const { container } = render(<CurveChart left={left} right={right} />);
  expect(container.querySelectorAll('.series.inlet path')).toHaveLength(0);
  expect(container.querySelectorAll('.series.inlet circle')).toHaveLength(2);
});
