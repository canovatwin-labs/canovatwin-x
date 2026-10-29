import type { Schema, Principal, Incident, RecordAnalysis, Agent, Page, Run, Audit } from './types';

const messages: Record<string, string> = {
  AUTHENTICATION_REQUIRED: 'Anahtar geçersiz veya oturum sona erdi. Yeniden bağlantı kurun.',
  WRITE_PERMISSION_REQUIRED: 'Bu işlem için yazma yetkili anahtar gerekiyor.',
  INVALID_REQUEST: 'Girilen bilgiler beklenen biçimde değil. Alanları kontrol edin.',
  CONFLICT: 'Kayıt başka bir işlemle değişmiş. Güncel durumu inceleyip yeniden deneyin.',
  INVALID_TRANSITION: 'Bu durum değişikliğine izin verilmiyor.',
  REPLAY_INCOMPATIBLE: 'Bu kaydın motor sürümü farklı; aynı motorla yeniden çalıştırılabilir.',
  STORAGE_BUSY: 'Kayıt alanı meşgul. Biraz sonra yeniden deneyin.',
  NOT_FOUND: 'İstenen kayıt bulunamadı.',
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public requestId = '',
  ) {
    super(
      messages[code] ??
        (status === 409
          ? 'Kayıt değişmiş veya işlem bu kayıtla uyumlu değil. Güncel durumu inceleyin.'
          : status === 404
            ? 'İstenen kayıt bulunamadı.'
            : status === 413
              ? 'İstek izin verilen boyutu aşıyor.'
              : status === 422
                ? 'Girilen bilgiler beklenen biçimde değil.'
                : 'İşlem tamamlanamadı. Servisi kontrol edip yeniden deneyin.'),
    );
  }
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Beklenmeyen bir hata oluştu.';
}

/** A session-scoped client: the key never enters URLs, browser storage or logs. */
export class ApiClient {
  private token: string;
  private pending = new Set<AbortController>();
  private closed = false;
  constructor(
    token: string,
    private onUnauthorized: () => void = () => {},
  ) {
    this.token = token;
  }
  close() {
    this.closed = true;
    this.token = '';
    this.pending.forEach((controller) => controller.abort());
    this.pending.clear();
  }
  async request<T>(path: string, body?: unknown): Promise<T> {
    if (this.closed) throw new Error('Oturum kapatıldı.');
    const controller = new AbortController();
    this.pending.add(controller);
    const timer = setTimeout(() => controller.abort(), 30_000);
    try {
      const response = await fetch(`/api/v1${path}`, {
        method: body === undefined ? 'GET' : 'POST',
        headers: {
          Authorization: `Bearer ${this.token}`,
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        credentials: 'omit',
        cache: 'no-store',
        redirect: 'error',
        signal: controller.signal,
      });
      const value: unknown = await response.json();
      if (this.closed) throw new Error('Oturum kapatıldı.');
      if (!response.ok) {
        const envelope = value as Partial<Schema['ErrorEnvelope']>;
        const error = new ApiError(
          response.status,
          envelope.error?.code ?? 'HTTP_ERROR',
          envelope.request_id ?? '',
        );
        if (response.status === 401) this.onUnauthorized();
        throw error;
      }
      return value as T;
    } catch (error) {
      if (error instanceof ApiError || this.closed) throw error;
      throw new Error(
        body === undefined
          ? 'Servise ulaşılamadı veya yanıt alınamadı. Bağlantıyı kontrol edip yeniden deneyin.'
          : 'İşlemin sonucu alınamadı; kayıt yapılmış olabilir. Tekrar göndermeden önce olay geçmişini kontrol edin.',
      );
    } finally {
      clearTimeout(timer);
      this.pending.delete(controller);
    }
  }
  session = () => this.request<Principal>('/session');
  health = () => this.request<Schema['Readiness']>('/health');
  agents = () => this.request<Agent[]>('/agents');
  incidents = (status: string, offset = 0) =>
    this.request<Page<Incident>>(
      `/incidents?limit=10&offset=${offset}${status ? `&status=${encodeURIComponent(status)}` : ''}`,
    );
  incident = (id: string) => this.request<Incident>(`/incidents/${encodeURIComponent(id)}`);
  runs = (id: string, offset = 0) =>
    this.request<Page<Run>>(`/incidents/${encodeURIComponent(id)}/runs?limit=10&offset=${offset}`);
  audit = (id: string, offset = 0) =>
    this.request<Page<Audit>>(
      `/incidents/${encodeURIComponent(id)}/audit?limit=10&offset=${offset}`,
    );
  run = (id: string) => this.request<RecordAnalysis>(`/runs/${encodeURIComponent(id)}`);
  analyze = (body: Pick<Schema['ScenarioBody'], 'scenario' | 'profile' | 'count' | 'seed'>) =>
    this.request<RecordAnalysis>('/analyses/scenario', body);
  transition = (id: string, body: Schema['StatusBody']) =>
    this.request<Incident>(`/incidents/${encodeURIComponent(id)}/status`, body);
  replay = (id: string) =>
    this.request<Schema['ReplayOutcome']>(`/runs/${encodeURIComponent(id)}/replay`, {});
}
