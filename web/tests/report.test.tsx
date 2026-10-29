import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ReportView, TraceView } from '../src/Report';
import { seriesSegments, TemperatureChart } from '../src/Telemetry';
import { data } from './fixtures';

describe('scientific meaning and result states', () => {
  it('shows a blocked run as no final report', () => {
    render(<ReportView record={data.blocked} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Çalışma engellendi');
    expect(screen.getByText('AGENT_BUDGET_EXCEEDED')).toBeVisible();
    expect(screen.queryByText('Analiz sonucu')).not.toBeInTheDocument();
  });
  it('distinguishes insufficient data from a clear result', () => {
    render(<ReportView record={data.insufficient} />);
    expect(screen.getByText('Veri yetersiz')).toBeVisible();
    expect(screen.getByText('Eksik veri analizi')).toBeVisible();
    expect(screen.queryByText('Belirti yok')).not.toBeInTheDocument();
  });
  it('renders source text as text rather than executable HTML', () => {
    const record = structuredClone(data.record);
    record.result.report!.summary = '<img src=x onerror="window.pwned=1">';
    const { container } = render(<ReportView record={record} />);
    expect(screen.getByText(record.result.report!.summary)).toBeVisible();
    expect(container.querySelector('img')).toBeNull();
  });
  it('supports legacy records with no research summary', () => {
    const record = structuredClone(data.record);
    record.result.report!.research = null;
    render(<ReportView record={record} />);
    expect(screen.getByText('Analiz sonucu')).toBeVisible();
    expect(screen.queryByText('Model değerlendirmesi')).toBeNull();
  });
  it('shows actual execution count separately from catalog capacity', () => {
    render(<TraceView record={data.record} agents={data.agents} />);
    expect(screen.getByText(/11 adım kaydı/)).toHaveTextContent('0 LLM çağrısı · 0 fiziksel komut');
    expect(screen.getAllByRole('listitem')).toHaveLength(11);
  });
  it('separates a failed activation attempt from completed agent work', () => {
    render(<TraceView record={data.blocked} agents={data.agents} />);
    expect(screen.getByText(/2 adım kaydı/)).toHaveTextContent(
      '1 tamamlanan · 1 başarısız · 1 araç çağrısı',
    );
  });
  it('breaks the line at null values instead of converting them to zero', () => {
    const samples = structuredClone(data.record.request.window.samples.slice(0, 4));
    samples[1]!.inlet_c = null;
    const segments = seriesSegments(samples, 'inlet_c');
    expect(segments.map((segment) => segment.length)).toEqual([1, 2]);
    expect(segments.flat().map((point) => point.x)).toEqual([0, 2, 3]);
    expect(segments.flat().some((point) => point.y === 0)).toBe(false);
  });
  it('preserves real time gaps without drawing a continuous interpolation', () => {
    const samples = structuredClone(data.record.request.window.samples.slice(0, 3));
    samples[2]!.timestamp = new Date(Date.parse(samples[0]!.timestamp) + 10_000).toISOString();
    expect(
      seriesSegments(samples, 'inlet_c').map((segment) => segment.map((point) => point.x)),
    ).toEqual([[0, 1], [10]]);
  });
  it('uses an accessible empty state for absent temperatures', () => {
    const samples = structuredClone(data.record.request.window.samples.slice(0, 3));
    samples.forEach((sample) => {
      sample.inlet_c = null;
      sample.reference_inlet_c = null;
    });
    render(<TemperatureChart samples={samples} />);
    expect(screen.getByText('Gösterilebilecek sıcaklık ölçümü yok.')).toBeVisible();
    expect(screen.queryByRole('img')).toBeNull();
  });
});
