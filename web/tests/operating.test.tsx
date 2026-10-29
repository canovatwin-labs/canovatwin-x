import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { NewAnalysis, IncidentList } from '../src/pages';
import { PlantSnapshot } from '../src/Overview';
import { TelemetryChart, seriesSegments } from '../src/Telemetry';
import { data, session } from './fixtures';

it('sends editable dynamic settings and updates the experiment briefing', async () => {
  const current = session();
  const analyze = vi.spyOn(current.api, 'analyze').mockResolvedValue(data.record);
  const user = userEvent.setup();
  render(<NewAnalysis session={current} />);
  await user.selectOptions(screen.getByLabelText('İş yükü profili'), 'batch');
  fireEvent.change(screen.getByLabelText('Temel IT yükü (kW)'), { target: { value: '6.4' } });
  fireEvent.change(screen.getByLabelText('Ortam sıcaklığı (°C)'), { target: { value: '35' } });
  fireEvent.change(screen.getByLabelText('Fan zaman sabiti (sn)'), { target: { value: '12' } });
  expect(screen.getByText('12 sn zaman sabiti')).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Analizi başlat ve kaydet' }));
  expect(analyze).toHaveBeenCalledExactlyOnceWith(
    expect.objectContaining({
      conditions: { workload: 'batch', baseline_load_kw: 6.4, ambient_c: 35, fan_response_s: 12 },
    }),
  );
});

it('reference mode omits dynamic settings and retains the original generator', async () => {
  const current = session();
  const analyze = vi.spyOn(current.api, 'analyze').mockResolvedValue(data.record);
  const user = userEvent.setup();
  render(<NewAnalysis session={current} />);
  await user.selectOptions(screen.getByLabelText('Simülasyon modeli'), 'reference');
  expect(screen.queryByLabelText('İş yükü profili')).toBeNull();
  await user.click(screen.getByRole('button', { name: 'Analizi başlat ve kaydet' }));
  expect(analyze).toHaveBeenCalledExactlyOnceWith({
    scenario: 'fan_loss',
    count: 360,
    seed: 42,
    profile: 'mvp12',
  });
});

it.each(['', '41'])('rejects invalid conditions (%s) without issuing a mutation', async (value) => {
  const current = session();
  const analyze = vi.spyOn(current.api, 'analyze');
  render(<NewAnalysis session={current} />);
  fireEvent.change(screen.getByLabelText('Ortam sıcaklığı (°C)'), { target: { value } });
  fireEvent.submit(
    screen.getByRole('button', { name: 'Analizi başlat ve kaydet' }).closest('form')!,
  );
  expect(await screen.findByRole('alert')).toHaveTextContent('Çalışma koşullarını');
  expect(analyze).not.toHaveBeenCalled();
});

it('shows missing last observations and warns about a stale snapshot', () => {
  const record = structuredClone(data.record);
  const last = record.request.window.samples.at(-1)!;
  last.inlet_c = null;
  record.request.as_of = new Date(Date.parse(last.timestamp) + 75_000).toISOString();
  render(<PlantSnapshot record={record} />);
  expect(screen.getByText('Giriş — °C')).toBeVisible();
  expect(screen.getByText(/75 sn gerisinde/)).toBeVisible();
  expect(screen.getByText('Canlı bağlantı yok')).toBeVisible();
});

it('shows persisted experiment conditions rather than form defaults', async () => {
  const record = structuredClone(data.record);
  record.generation = {
    generator_version: 'dynamic-1.0',
    scenario: 'fan_loss',
    seed: 17,
    count: 120,
    start: record.request.window.samples[0]!.timestamp,
    conditions: { workload: 'batch', baseline_load_kw: 6, ambient_c: 35, fan_response_s: 12 },
  };
  const user = userEvent.setup();
  render(<PlantSnapshot record={record} />);
  await user.click(screen.getByText('Kayıtlı deney koşulları'));
  expect(screen.getByText('12 sn')).toBeVisible();
  expect(screen.getByText(/Toplu işlem · Tohum 17/)).toBeVisible();
});

it('gives each chart a unique accessible title and preserves missing power readings', () => {
  const samples = structuredClone(data.record.request.window.samples.slice(0, 3));
  samples[1]!.cooling_kw = null;
  expect(seriesSegments(samples, 'cooling_kw').map((s) => s.length)).toEqual([1, 1]);
  render(
    <>
      <TelemetryChart samples={samples} kind="power" />
      <TelemetryChart samples={samples} kind="fan" />
    </>,
  );
  const power = screen.getByRole('img', { name: /Sentetik IT yükü ve soğutma gücü/ });
  const fan = screen.getByRole('img', { name: /Sentetik fan komutu ve geri bildirimi/ });
  expect(power.getAttribute('aria-labelledby')).not.toEqual(fan.getAttribute('aria-labelledby'));
});

it('renders actual latest run data while queue counters remain page scoped', async () => {
  const current = session();
  vi.spyOn(current.api, 'incidents').mockResolvedValue({
    items: [data.incident],
    limit: 10,
    offset: 0,
  });
  const run = vi.spyOn(current.api, 'run').mockResolvedValue(data.record);
  render(<IncidentList api={current.api} />);
  expect(await screen.findByRole('img', { name: /Sentetik IT yükü/ })).toBeVisible();
  expect(run).toHaveBeenCalledWith(data.incident.latest_run_id);
  const label = screen.getByText('Görüntülenen kayıt');
  expect(within(label.parentElement!).getByText('1')).toBeVisible();
  expect(screen.getByText('Sayfa 1 · Seçili filtre')).toBeVisible();
});
