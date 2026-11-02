import { act, render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';
import { Comparison, comparisonLink } from '../src/Comparison';
import { ApiClient, ApiError } from '../src/api/client';
import { data, deferred, session } from './fixtures';
import fixture from './fixtures/comparison.json';
import type { Schema } from '../src/api/types';
const result = fixture as Schema['RunComparison'];

describe('recorded comparison workspace', () => {
  it('opens an authenticated comparison deep link through the application router', async () => {
    window.location.hash = comparisonLink('RUN-baseline', 'RUN-candidate').slice(1);
    const fetch = vi.mocked(globalThis.fetch).mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith('/session'))
        return new Response(JSON.stringify({ role: 'reader', actor: 'api-reader' }));
      if (path.endsWith('/health')) return new Response(JSON.stringify(data.health));
      if (path === '/api/v1/comparisons?baseline=RUN-baseline&candidate=RUN-candidate')
        return new Response(JSON.stringify(result));
      throw new Error('Unexpected request: ' + path);
    });
    render(<App />);
    await userEvent.type(screen.getByLabelText('Erişim anahtarı'), 'R'.repeat(32));
    await userEvent.click(screen.getByRole('button', { name: 'Çalışma alanını aç' }));
    expect(await screen.findByRole('region', { name: 'Karşılaştırma sonucu' })).toBeVisible();
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/comparisons?baseline=RUN-baseline&candidate=RUN-candidate',
      expect.objectContaining({ method: 'GET' }),
    );
    expect(screen.getByRole('link', { name: 'Koşum karşılaştırması' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });
  it('does not fetch until two distinct records are selected', async () => {
    const api = session('reader').api;
    const compare = vi.spyOn(api, 'compare');
    render(<Comparison api={api} initialBaseline="RUN-baseline" />);
    expect(screen.getByText(/İki kayıt seçildiğinde/)).toBeVisible();
    await userEvent.type(screen.getByLabelText('Aday çalışma kimliği'), 'RUN-baseline');
    await userEvent.click(screen.getByRole('button', { name: 'Kayıtları karşılaştır' }));
    expect(screen.getByRole('alert')).toHaveTextContent('iki farklı');
    expect(screen.getByLabelText('Aday çalışma kimliği')).toHaveFocus();
    expect(compare).not.toHaveBeenCalled();
  });
  it('focuses and describes an invalid baseline without making a request', async () => {
    const api = session().api;
    const compare = vi.spyOn(api, 'compare');
    render(<Comparison api={api} initialBaseline="invalid/id" initialCandidate="RUN-candidate" />);
    await userEvent.click(screen.getByRole('button', { name: 'Kayıtları karşılaştır' }));
    expect(screen.getByLabelText('Temel çalışma kimliği')).toHaveFocus();
    expect(screen.getByLabelText('Temel çalışma kimliği')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText('Temel çalışma kimliği')).toHaveAccessibleDescription(
      /iki farklı/,
    );
    expect(compare).not.toHaveBeenCalled();
  });
  it('supports reader deep links and preserves missing values and direction', async () => {
    const api = session('reader').api;
    const compare = vi.spyOn(api, 'compare').mockResolvedValue(result);
    render(
      <Comparison api={api} initialBaseline="RUN-baseline" initialCandidate="RUN-candidate" />,
    );
    const output = await screen.findByRole('region', { name: 'Karşılaştırma sonucu' });
    expect(compare).toHaveBeenCalledWith('RUN-baseline', 'RUN-candidate');
    const humidity = within(output).getByRole('row', { name: /Bağıl nem/ });
    expect(within(humidity).getAllByRole('cell')[1]).toHaveTextContent('— · — · 30 / 30');
    expect(within(humidity).getAllByRole('cell')[1]).toHaveTextContent('Min: — · Maks: —');
    expect(within(output).getByText('Fark yönü: aday − temel')).toBeVisible();
    expect(within(output).getAllByText(/elektrik tasarrufu/)).toHaveLength(1);
  });
  it('reports incompatible records and retries without writing history', async () => {
    const api = session().api;
    const compare = vi
      .spyOn(api, 'compare')
      .mockRejectedValueOnce(new ApiError(409, 'COMPARISON_INCOMPATIBLE'))
      .mockResolvedValueOnce(result);
    render(
      <Comparison api={api} initialBaseline="RUN-baseline" initialCandidate="RUN-candidate" />,
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('karşılaştırılamıyor');
    await userEvent.click(screen.getByRole('button', { name: 'Yeniden dene' }));
    expect(await screen.findByRole('region', { name: 'Karşılaştırma sonucu' })).toBeVisible();
    expect(compare).toHaveBeenCalledTimes(2);
  });
  it('discards an old response when the selection is edited', async () => {
    const api = session().api;
    const pending = deferred<Schema['RunComparison']>();
    vi.spyOn(api, 'compare').mockReturnValue(pending.promise);
    render(
      <Comparison api={api} initialBaseline="RUN-baseline" initialCandidate="RUN-candidate" />,
    );
    await userEvent.clear(screen.getByLabelText('Aday çalışma kimliği'));
    await act(async () => pending.resolve(result));
    await waitFor(() => expect(screen.getByText(/İki kayıt seçildiğinde/)).toBeVisible());
    expect(screen.queryByRole('region', { name: 'Karşılaştırma sonucu' })).not.toBeInTheDocument();
  });
  it('exports the exact comparison contract without session credentials', async () => {
    const api = session('reader').api;
    vi.spyOn(api, 'compare').mockResolvedValue(result);
    const create = vi.fn((_blob: Blob) => 'blob:test-comparison');
    const revoke = vi.fn();
    vi.stubGlobal(
      'URL',
      Object.assign(class extends URL {}, { createObjectURL: create, revokeObjectURL: revoke }),
    );
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    render(
      <Comparison api={api} initialBaseline="RUN-baseline" initialCandidate="RUN-candidate" />,
    );
    await userEvent.click(
      await screen.findByRole('button', { name: 'Karşılaştırmayı JSON indir' }),
    );
    const blob = create.mock.calls[0]?.[0] as Blob;
    expect(blob.type).toBe('application/json');
    const content = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.readAsText(blob);
    });
    expect(JSON.parse(content)).toEqual(result);
    expect(content).not.toContain('test-session-key');
    expect(click).toHaveBeenCalledOnce();
    const anchor = click.mock.instances[0] as HTMLAnchorElement;
    expect(anchor.download).toBe('comparison-RUN-baseline-RUN-candidate.json');
    await waitFor(() => expect(revoke).toHaveBeenCalledWith('blob:test-comparison'));
  });
  it('encodes selections without putting the credential into the URL', async () => {
    const fetch = vi.mocked(globalThis.fetch).mockResolvedValue(new Response('{}'));
    const api = new ApiClient('private-test-key');
    await api.compare('RUN-a&x=1', 'RUN-b?next=1');
    expect(String(fetch.mock.calls[0]![0])).toBe(
      '/api/v1/comparisons?baseline=RUN-a%26x%3D1&candidate=RUN-b%3Fnext%3D1',
    );
    expect(comparisonLink('RUN-baseline', 'RUN-candidate')).toBe(
      '#/compare?baseline=RUN-baseline&candidate=RUN-candidate',
    );
    api.close();
  });
});
