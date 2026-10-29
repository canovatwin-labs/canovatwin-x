import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiClient, ApiError } from '../src/api/client';
import { deferred } from './fixtures';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
const response = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

describe('session-scoped API client', () => {
  it('uses relative URLs and headers, with no cookies, cache or token storage', async () => {
    const fetch = vi.fn().mockResolvedValue(response({ role: 'reader', actor: 'api-reader' }));
    vi.stubGlobal('fetch', fetch);
    const setLocal = vi.spyOn(Storage.prototype, 'setItem');
    const client = new ApiClient('secret');
    expect(await client.session()).toEqual({ role: 'reader', actor: 'api-reader' });
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/session',
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer secret' },
        credentials: 'omit',
        cache: 'no-store',
        redirect: 'error',
      }),
    );
    expect(setLocal).not.toHaveBeenCalled();
    client.close();
  });
  it.each([
    [401, 'AUTHENTICATION_REQUIRED'],
    [403, 'WRITE_PERMISSION_REQUIRED'],
    [409, 'CONFLICT'],
    [503, 'STORAGE_BUSY'],
  ])('preserves HTTP%s as a safe failure', async (status, code) => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          response(
            { request_id: 'request-1', error: { code, message: 'PRIVATE /path database content' } },
            status as number,
          ),
        ),
    );
    const unauthorized = vi.fn();
    const client = new ApiClient('secret', unauthorized);
    const error = await client.session().catch((issue) => issue);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(status);
    expect(error.requestId).toBe('request-1');
    expect(error.message).not.toContain('PRIVATE');
    expect(unauthorized).toHaveBeenCalledTimes(status === 401 ? 1 : 0);
    client.close();
  });
  it('does not retry a mutation whose outcome is unknown', async () => {
    const fetch = vi.fn().mockRejectedValue(new TypeError('connection lost'));
    vi.stubGlobal('fetch', fetch);
    const client = new ApiClient('secret');
    await expect(client.replay('run1')).rejects.toThrow('kayıt yapılmış olabilir');
    expect(fetch).toHaveBeenCalledTimes(1);
    client.close();
  });
  it('aborts pending requests and discards late responses after logout', async () => {
    const late = deferred<Response>();
    const fetch = vi.fn().mockReturnValue(late.promise);
    vi.stubGlobal('fetch', fetch);
    const unauthorized = vi.fn();
    const client = new ApiClient('secret', unauthorized);
    const result = client.session().catch((error) => error);
    client.close();
    const signal = fetch.mock.calls[0]![1].signal as AbortSignal;
    expect(signal.aborted).toBe(true);
    late.resolve(response({ role: 'writer' }));
    expect(await result).toBeInstanceOf(Error);
    expect(unauthorized).not.toHaveBeenCalled();
    await expect(client.session()).rejects.toThrow('Oturum kapatıldı');
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it('bounds waiting time and aborts the underlying request', async () => {
    vi.useFakeTimers();
    let signal: AbortSignal | undefined;
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url, options: RequestInit) =>
          new Promise((_resolve, reject) => {
            signal = options.signal!;
            signal.addEventListener('abort', () => reject(new Error('aborted')));
          }),
      ),
    );
    const client = new ApiClient('secret');
    const outcome = client.health().catch((error) => error);
    await vi.advanceTimersByTimeAsync(30_000);
    expect(signal?.aborted).toBe(true);
    expect((await outcome).message).toContain('Servise ulaşılamadı');
    client.close();
  });
  it('encodes resource identifiers and keeps mutation fields in JSON', async () => {
    const fetch = vi.fn().mockResolvedValue(response({}));
    vi.stubGlobal('fetch', fetch);
    const client = new ApiClient('secret');
    await client.transition('id /?', {
      target: 'closed',
      expected_revision: 3,
      reason: 'İncelendi',
    });
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/incidents/id%20%2F%3F/status',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ target: 'closed', expected_revision: 3, reason: 'İncelendi' }),
      }),
    );
    client.close();
  });
});
