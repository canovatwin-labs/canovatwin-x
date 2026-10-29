import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';
import { ApiClient, ApiError } from '../src/api/client';
import { IncidentDetail } from '../src/IncidentDetail';
import { AgentCatalog, IncidentList, NewAnalysis } from '../src/pages';
import { data, deferred, session } from './fixtures';

function detailMocks(current = session()) {
  vi.spyOn(current.api, 'incident').mockResolvedValue(data.incident);
  vi.spyOn(current.api, 'runs').mockResolvedValue(data.runs);
  vi.spyOn(current.api, 'audit').mockResolvedValue(data.audit);
  vi.spyOn(current.api, 'agents').mockResolvedValue(data.agents);
  vi.spyOn(current.api, 'run').mockResolvedValue(data.record);
  return current;
}

describe('operator workflows', () => {
  it('connects using server-verified role and clears session on logout', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      const value = path.endsWith('/session')
        ? { role: 'reader', actor: 'api-reader' }
        : path.endsWith('/health')
          ? data.health
          : { items: [], limit: 10, offset: 0 };
      return new Response(JSON.stringify(value), { status: 200 });
    });
    const close = vi.spyOn(ApiClient.prototype, 'close');
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText('Erişim anahtarı'), 'R'.repeat(32));
    await user.click(screen.getByRole('button', { name: 'Çalışma alanını aç' }));
    expect(await screen.findByText('Salt okunur')).toBeVisible();
    expect(screen.queryByLabelText('Erişim anahtarı')).toBeNull();
    await user.click(screen.getByRole('button', { name: 'Oturumu kapat' }));
    expect(screen.getByLabelText('Erişim anahtarı')).toHaveValue('');
    expect(close).toHaveBeenCalled();
    expect(fetch).toHaveBeenCalled();
    expect(screen.queryByText('Olay incelemeleri', { selector: 'h1' })).toBeNull();
  });
  it('disables mutating actions for readers', () => {
    render(<NewAnalysis session={session('reader')} />);
    expect(screen.getByRole('button', { name: 'Analizi başlat ve kaydet' })).toBeDisabled();
    expect(screen.getByLabelText('Senaryo')).toBeDisabled();
  });
  it('submits typed scenario configuration once and prevents double submission', async () => {
    const current = session();
    const pending = deferred<typeof data.record>();
    const analyze = vi.spyOn(current.api, 'analyze').mockReturnValue(pending.promise);
    const user = userEvent.setup();
    render(<NewAnalysis session={current} />);
    await user.selectOptions(screen.getByLabelText('Senaryo'), 'cooling_loss');
    await user.selectOptions(screen.getByLabelText('Uzman profili'), 'core6');
    const button = screen.getByRole('button', { name: 'Analizi başlat ve kaydet' });
    await user.dblClick(button);
    expect(analyze).toHaveBeenCalledExactlyOnceWith({
      scenario: 'cooling_loss',
      profile: 'core6',
      count: 360,
      conditions: { workload: 'cyclic', baseline_load_kw: 4.2, ambient_c: 30, fan_response_s: 6 },
      seed: 42,
    });
    expect(screen.getByRole('button', { name: /Analiz çalışıyor/ })).toBeDisabled();
    await act(async () => pending.resolve(data.record));
    expect(window.location.hash).toContain(data.incident.incident_id);
  });
  it('does not redirect to an old analysis after leaving the form', async () => {
    const current = session();
    const pending = deferred<typeof data.record>();
    vi.spyOn(current.api, 'analyze').mockReturnValue(pending.promise);
    const { unmount } = render(<NewAnalysis session={current} />);
    fireEvent.submit(
      screen.getByRole('button', { name: 'Analizi başlat ve kaydet' }).closest('form')!,
    );
    unmount();
    window.location.hash = '/agents';
    await act(async () => pending.resolve(data.record));
    expect(window.location.hash).toBe('#/agents');
  });
  it('rejects unsafe numeric seeds without calling the API', async () => {
    const current = session();
    const analyze = vi.spyOn(current.api, 'analyze');
    render(<NewAnalysis session={current} />);
    fireEvent.change(screen.getByLabelText('Rastgelelik tohumu'), {
      target: { value: '9999999999999999999' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Analizi başlat ve kaydet' }).closest('form')!,
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('güvenli bir tam sayı');
    expect(analyze).not.toHaveBeenCalled();
  });
  it('resets pagination when filtering and never claims a global incident total', async () => {
    const current = session();
    const list = vi.spyOn(current.api, 'incidents').mockResolvedValue({
      items: Array.from({ length: 10 }, (_, index) => ({
        ...data.incident,
        incident_id: `incident-${index}`,
      })),
      limit: 10,
      offset: 0,
    });
    const user = userEvent.setup();
    render(<IncidentList api={current.api} />);
    await screen.findByText('Sayfa 1 · Bu sayfada 10 kayıt');
    await user.click(screen.getByRole('button', { name: 'Sonraki' }));
    await waitFor(() => expect(list).toHaveBeenLastCalledWith('', 10));
    await user.selectOptions(screen.getByLabelText('Durum filtresi'), 'closed');
    await waitFor(() => expect(list).toHaveBeenLastCalledWith('closed', 0));
    expect(screen.getByText('Sayfa 1 · Bu sayfada 10 kayıt')).toBeVisible();
  });
  it('renders 36 catalog roles and separates 12 implemented from planned', async () => {
    const current = session();
    vi.spyOn(current.api, 'agents').mockResolvedValue(data.agents);
    render(<AgentCatalog api={current.api} />);
    await screen.findByText('Kayıtlı rol');
    expect(screen.getAllByText('Uygulanmış', { exact: true })).toHaveLength(12);
    expect(screen.getAllByText('Planlı', { exact: true })).toHaveLength(24);
    expect(screen.getByText('36')).toBeVisible();
  });
  it('retains typed reason on conflict, refreshes revision, and does not retry a write', async () => {
    const current = detailMocks();
    const get = vi.mocked(current.api.incident);
    get.mockResolvedValueOnce(data.incident).mockResolvedValue({ ...data.incident, revision: 2 });
    const write = vi
      .spyOn(current.api, 'transition')
      .mockRejectedValue(new ApiError(409, 'CONFLICT'));
    const user = userEvent.setup();
    render(<IncidentDetail session={current} id={data.incident.incident_id} />);
    await user.type(await screen.findByLabelText('İnceleme gerekçesi'), 'Kontrol edildi');
    await user.click(screen.getByRole('button', { name: 'Durumu kaydet' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Kayıt başka bir işlemle değişmiş');
    await waitFor(() => expect(screen.getByText('Beklenen revizyon: 2')).toBeVisible());
    expect(screen.getByLabelText('İnceleme gerekçesi')).toHaveValue('Kontrol edildi');
    expect(write).toHaveBeenCalledExactlyOnceWith(data.incident.incident_id, {
      target: 'investigating',
      expected_revision: 1,
      reason: 'Kontrol edildi',
    });
  });
  it('offers only permitted workflow transitions and sends the current revision', async () => {
    const current = detailMocks();
    vi.mocked(current.api.incident).mockResolvedValue({
      ...data.incident,
      status: 'investigating',
      revision: 3,
    });
    const write = vi
      .spyOn(current.api, 'transition')
      .mockResolvedValue({ ...data.incident, status: 'closed', revision: 4 });
    const user = userEvent.setup();
    render(<IncidentDetail session={current} id={data.incident.incident_id} />);
    const target = await screen.findByLabelText('Yeni durum');
    expect(
      within(target)
        .getAllByRole('option')
        .map((option) => option.textContent),
    ).toEqual(['Açık', 'Kapalı']);
    await user.selectOptions(target, 'closed');
    await user.type(screen.getByLabelText('İnceleme gerekçesi'), 'İnceleme bitti');
    await user.click(screen.getByRole('button', { name: 'Durumu kaydet' }));
    expect(write).toHaveBeenCalledExactlyOnceWith(data.incident.incident_id, {
      target: 'closed',
      expected_revision: 3,
      reason: 'İnceleme bitti',
    });
    expect(await screen.findByText('İnceleme durumu gerekçesiyle kaydedildi.')).toBeVisible();
  });
  it('shows replay differences as a review outcome rather than an HTTP success claim', async () => {
    const current = detailMocks();
    const replay = vi.spyOn(current.api, 'replay').mockResolvedValue({
      record: { ...data.record, run_id: 'new-replay' },
      matches: false,
      differences: ['report.summary'],
    });
    const user = userEvent.setup();
    render(<IncidentDetail session={current} id={data.incident.incident_id} />);
    await user.click(await screen.findByRole('button', { name: 'Kaydı yeniden analiz et' }));
    expect(await screen.findByText('report.summary')).toBeVisible();
    expect(screen.getByRole('status')).toHaveTextContent('farklar var');
    expect(replay).toHaveBeenCalledOnce();
  });
  it('supports arrow-key tabs and exposes selected tab semantics', async () => {
    const user = userEvent.setup();
    render(<IncidentDetail session={detailMocks()} id={data.incident.incident_id} />);
    const report = await screen.findByRole('tab', { name: 'Rapor' });
    report.focus();
    await user.keyboard('{ArrowRight}');
    const telemetry = screen.getByRole('tab', { name: 'Telemetri' });
    expect(telemetry).toHaveFocus();
    expect(telemetry).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tabpanel')).toHaveAccessibleName('Telemetri');
    await user.keyboard('{End}');
    expect(screen.getByRole('tab', { name: 'Geçmiş' })).toHaveFocus();
  });
});
