import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Operations } from '../src/Operations';
import { data, session } from './fixtures';

describe('operations center', () => {
  it('shows recorded counts and honest empty states without fabricated telemetry', async () => {
    const api = session('reader').api;
    vi.spyOn(api, 'agents').mockResolvedValue(data.agents);
    vi.spyOn(api, 'incidents').mockResolvedValue({ items: [], limit: 10, offset: 0 });
    const run = vi.spyOn(api, 'run');
    render(<Operations api={api} />);
    expect(await screen.findByText('İlk ölçüm penceresiyle başlayın')).toBeVisible();
    expect(screen.getAllByText('Henüz ölçüm kaydedilmedi')).toHaveLength(2);
    expect(screen.getByRole('img')).toHaveAccessibleName(
      'Son 0 olay: 0 açık veya inceleniyor, 0 kapalı',
    );
    expect(run).not.toHaveBeenCalled();
  });
  it('renders only the stored window and clearly bounds incident statistics', async () => {
    const api = session().api;
    vi.spyOn(api, 'agents').mockResolvedValue(data.agents);
    vi.spyOn(api, 'incidents').mockResolvedValue({ items: [data.incident], limit: 10, offset: 0 });
    const run = vi.spyOn(api, 'run').mockResolvedValue(data.record);
    render(<Operations api={api} />);
    expect(await screen.findByText('Kaydedilmiş tesis görünümü')).toBeVisible();
    expect(await screen.findByText('Canlı bağlantı yok')).toBeVisible();
    expect(run).toHaveBeenCalledWith(data.incident.latest_run_id);
    expect(screen.getByText('Son 10 olayın açık ve incelenen kayıtları')).toBeVisible();
  });
  it('surfaces failed overview requests with a retry action', async () => {
    const api = session().api;
    vi.spyOn(api, 'agents').mockRejectedValue(new Error('Katalog okunamadı'));
    vi.spyOn(api, 'incidents').mockResolvedValue({ items: [], limit: 10, offset: 0 });
    render(<Operations api={api} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Katalog okunamadı');
    expect(screen.queryByText('Kayıtlı analiz')).not.toBeInTheDocument();
  });
});

import { fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TelemetryChart } from '../src/Telemetry';

describe('interactive measurement charts', () => {
  it('toggles series without changing or imputing the measurements', async () => {
    const { container } = render(<TelemetryChart samples={data.record.request.window.samples} />);
    const toggle = screen.getByRole('button', { name: 'Referans' });
    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    expect(container.querySelector('.series.reference')).toHaveAttribute('visibility', 'hidden');
    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
  });
  it('reads the selected stored sample and leaves missing readings explicit', () => {
    const samples = structuredClone(data.record.request.window.samples.slice(0, 3));
    samples[2]!.inlet_c = null;
    render(<TelemetryChart samples={samples} />);
    fireEvent.change(screen.getByRole('slider', { name: 'Sıcaklık seyri ölçüm seçimi' }), {
      target: { value: '2' },
    });
    expect(screen.getByRole('status')).toHaveTextContent('Giriş: — °C');
  });
});
