import { act, renderHook, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useLoad } from '../src/hooks';
import { deferred } from './fixtures';

it('ignores stale data arriving after navigation', async () => {
  const old = deferred<string>();
  const fresh = deferred<string>();
  const { result, rerender } = renderHook(
    ({ id }) => useLoad(() => (id === 1 ? old.promise : fresh.promise), [id]),
    { initialProps: { id: 1 } },
  );
  rerender({ id: 2 });
  await act(async () => fresh.resolve('current'));
  await waitFor(() => expect(result.current.data).toBe('current'));
  await act(async () => old.resolve('stale'));
  expect(result.current.data).toBe('current');
});
it('ignores stale errors and handles rejection without unhandled promises', async () => {
  const old = deferred<string>();
  const load = vi.fn().mockReturnValueOnce(old.promise).mockResolvedValueOnce('fresh');
  const { result, rerender } = renderHook(({ id }) => useLoad(load, [id]), {
    initialProps: { id: 1 },
  });
  rerender({ id: 2 });
  await waitFor(() => expect(result.current.data).toBe('fresh'));
  await act(async () => old.reject(new Error('stale failure')));
  expect(result.current.error).toBeUndefined();
});
