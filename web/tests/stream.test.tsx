import { waitFor, act, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { RecordAnalysis, Schema } from '../src/api/types';
import { StreamLab, StreamResult, StreamRun } from '../src/StreamLab';
import { data, deferred, session } from './fixtures';

function streamRecord(): RecordAnalysis {
  const timestamp = data.record.request.window.samples[0]!.timestamp;
  const state: Schema['StreamState'] = {
    committed: 3,
    pending: 0,
    connection: 'connected',
    freshness: 'fresh',
    last_arrival_at: timestamp,
    last_measurement_at: timestamp,
    watermark_at: timestamp,
  };
  return {
    ...data.record,
    stream_experiment: {
      recipe: {
        replay_version: 'transport-1.0',
        delivery: 'jitter',
        generation: {
          asset_id: 'synthetic-unit-01',
          generator_version: 'dynamic-1.0',
          scenario: 'normal',
          count: 120,
          seed: 42,
          start: timestamp,
          conditions: {
            workload: 'cyclic',
            baseline_load_kw: 4.2,
            ambient_c: 30,
            fan_response_s: 6,
          },
        },
      },
      config: {
        asset_id: data.record.request.window.asset_id,
        max_lateness_s: 2,
        future_tolerance_s: 5,
        stale_after_s: 10,
        max_pending: 600,
      },
      as_of: timestamp,
      generated: 3,
      accepted: 3,
      rejected: 1,
      dropped: 0,
      final_state: state,
      window: data.record.request.window,
      trace_sha256: 'a'.repeat(64),
      events: [
        {
          sequence: 1,
          at: timestamp,
          measurement_at: timestamp,
          sample_id: 'sample-first',
          outcome: 'accepted',
          reason: null,
          state,
        },
        {
          sequence: 2,
          at: timestamp,
          measurement_at: timestamp,
          sample_id: 'sample-repeat',
          outcome: 'rejected',
          reason: 'duplicate_id',
          state,
        },
      ],
    },
  };
}

describe('stream workspace', () => {
  it('blocks creation for read-only sessions', () => {
    render(<StreamLab session={session('reader')} />);
    expect(
      screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }),
    ).toBeDisabled();
    expect(screen.getByLabelText('Aktarım profili')).toBeDisabled();
  });
  it('submits the chosen physical and delivery recipes once and opens the saved run', async () => {
    const current = session();
    const pending = deferred<RecordAnalysis>();
    const run = vi.spyOn(current.api, 'streamExperiment').mockReturnValue(pending.promise);
    const user = userEvent.setup();
    render(<StreamLab session={current} />);
    await screen.findByLabelText('Ekipman');
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }),
      ).toBeEnabled(),
    );
    await user.selectOptions(screen.getByLabelText('Fiziksel senaryo'), 'fan_loss');
    await user.selectOptions(screen.getByLabelText('Aktarım profili'), 'outage');
    await user.dblClick(
      screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }),
    );
    expect(run).toHaveBeenCalledExactlyOnceWith({
      asset_id: 'synthetic-unit-01',
      profile: 'mvp12',
      start: null,
      scenario: 'fan_loss',
      delivery: 'outage',
      count: 120,
      seed: 42,
      conditions: { workload: 'cyclic', baseline_load_kw: 4.2, ambient_c: 30, fan_response_s: 6 },
    });
    expect(screen.getByRole('button', { name: /Deney çalışıyor/ })).toBeDisabled();
    await act(async () => pending.resolve(data.record));
    expect(window.location.hash).toBe(`#/stream/${data.record.run_id}`);
  });
  it('retains user input on failure without automatically retrying', async () => {
    const current = session();
    const run = vi
      .spyOn(current.api, 'streamExperiment')
      .mockRejectedValue(new Error('Bağlantı kesildi'));
    const user = userEvent.setup();
    render(<StreamLab session={current} />);
    await screen.findByLabelText('Ekipman');
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }),
      ).toBeEnabled(),
    );
    await user.click(screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Bağlantı kesildi');
    expect(screen.getByLabelText('Aktarım profili')).toHaveValue('jitter');
    expect(run).toHaveBeenCalledOnce();
  });
  it('rejects unsafe seeds before sending the experiment', async () => {
    const current = session();
    const run = vi.spyOn(current.api, 'streamExperiment');
    render(<StreamLab session={current} />);
    await screen.findByLabelText('Ekipman');
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }),
      ).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText('Rastgelelik tohumu'), {
      target: { value: '999999999999999999' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Aktarım deneyini çalıştır ve kaydet' }).closest('form')!,
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('güvenli bir tam sayı');
    expect(run).not.toHaveBeenCalled();
  });
  it('shows exceptions first and exposes every accepted event when requested', async () => {
    const record = streamRecord();
    render(<StreamResult record={record} />);
    expect(screen.queryByText('sample-first')).toBeNull();
    expect(screen.getByText('Tekrar ölçüm kimliği')).toBeVisible();
    await userEvent.click(screen.getByLabelText('Kabul dışındaki olaylar'));
    expect(screen.getByText('sample-first')).toBeVisible();
    expect(screen.getByRole('link', { name: 'Kanıt ve raporu aç' })).toHaveAttribute(
      'href',
      `#/incidents/${record.result.incident_id}`,
    );
    expect(screen.getByText(/Tazelik bu deneyin sanal saatinde/)).toBeVisible();
  });
  it('loads a saved result after navigation and handles ordinary runs clearly', async () => {
    const current = session();
    vi.spyOn(current.api, 'run').mockResolvedValue(data.record);
    render(<StreamRun session={current} id={data.record.run_id} />);
    expect(await screen.findByText(/Bu çalışma bir aktarım deneyi içermiyor/)).toBeVisible();
  });
});
