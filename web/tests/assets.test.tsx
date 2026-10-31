import { waitFor, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { AssetList, AssetWorkspace } from '../src/Assets';
import { NewAnalysis } from '../src/pages';
import { ApiClient } from '../src/api/client';
import { assetPage, data, session } from './fixtures';

describe('asset workspace', () => {
  it('shows configured units without claiming measurements exist', async () => {
    render(<AssetList api={session().api} />);
    expect(await screen.findByRole('link', { name: 'Pilot 02' })).toHaveAttribute(
      'href',
      '#/assets/synthetic-unit-02',
    );
    expect(screen.getAllByText('Henüz ölçüm yok')).toHaveLength(2);
  });
  it('selects an equipment target independently from the physical fault', async () => {
    const current = session();
    const analyze = vi.spyOn(current.api, 'analyze').mockResolvedValue(data.record);
    render(<NewAnalysis session={current} initialAsset="synthetic-unit-02" />);
    const selector = await screen.findByLabelText('Ekipman');
    expect(selector).toHaveValue('synthetic-unit-02');
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Analizi başlat ve kaydet' })).toBeEnabled(),
    );
    await userEvent.selectOptions(screen.getByLabelText('Senaryo'), 'cooling_loss');
    await userEvent.click(screen.getByRole('button', { name: 'Analizi başlat ve kaydet' }));
    expect(analyze).toHaveBeenCalledExactlyOnceWith(
      expect.objectContaining({ asset_id: 'synthetic-unit-02', scenario: 'cooling_loss' }),
    );
  });
  it('keeps unknown targets blocked instead of silently selecting a different unit', async () => {
    render(<NewAnalysis session={session()} initialAsset="unknown" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('yapılandırılmış katalogda yok');
    expect(screen.getByRole('button', { name: 'Analizi başlat ve kaydet' })).toBeDisabled();
  });
  it('shows the exact asset record and preserves a missing latest reading', async () => {
    const current = session('reader');
    const record = structuredClone(data.record);
    record.request.window.samples.at(-1)!.inlet_c = null;
    vi.spyOn(current.api, 'asset').mockResolvedValue({
      catalog_version: 'catalog-1.0',
      asset: { ...assetPage.items[0]!, latest_run_id: record.run_id, run_count: 1 },
      channels: [
        {
          field: 'inlet_c',
          name: 'Giriş sıcaklığı',
          unit: '°C',
          illustrative_min: -20,
          illustrative_max: 80,
        },
      ],
    });
    vi.spyOn(current.api, 'run').mockResolvedValue(record);
    const incidents = vi
      .spyOn(current.api, 'assetIncidents')
      .mockResolvedValue({ ...data.runs, items: [data.incident] });
    render(<AssetWorkspace session={current} id={record.request.window.asset_id} />);
    const row = await screen.findByRole('row', { name: /Giriş sıcaklığı/ });
    expect(within(row).getAllByRole('cell')[3]).toHaveTextContent('—');
    expect(incidents).toHaveBeenCalledWith(record.request.window.asset_id, 0);
    expect(screen.getByText(/Canlı ölçüm değildir/)).toBeVisible();
  });
  it('uses query encoding for legacy asset IDs and never places credentials in URLs', async () => {
    const fetch = vi.mocked(globalThis.fetch).mockResolvedValue(new Response('{}'));
    const api = new ApiClient('private-test-key');
    await api.asset('ünite/a?x=1&y=2');
    expect(String(fetch.mock.calls[0]![0])).toBe(
      '/api/v1/assets/detail?asset_id=%C3%BCnite%2Fa%3Fx%3D1%26y%3D2',
    );
    api.close();
  });
});
