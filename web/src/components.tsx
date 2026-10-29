import type { ReactNode } from 'react';
import { ApiError, errorMessage } from './api/client';
import { label } from './labels';

export function Badge({ value }: { value: string | null | undefined }) {
  const tone = ['completed', 'clear', 'active', 'closed'].includes(value ?? '')
    ? 'good'
    : ['blocked', 'failed'].includes(value ?? '')
      ? 'danger'
      : ['needs_review', 'insufficient_data', 'uncertain'].includes(value ?? '')
        ? 'warn'
        : 'neutral';
  return <span className={`badge ${tone}`}>{label(value)}</span>;
}
export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <div className="notice danger" role="alert">
      <p>{errorMessage(error)}</p>
      {error instanceof ApiError && error.requestId && (
        <small>
          Destek kimliği: <span className="mono">{error.requestId}</span>
        </small>
      )}
      {retry && (
        <button className="secondary" onClick={retry}>
          Yeniden dene
        </button>
      )}
    </div>
  );
}
export function Loading() {
  return (
    <div className="empty" role="status">
      Veriler yükleniyor…
    </div>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}
export function PageHeading({
  kicker,
  title,
  children,
  action,
}: {
  kicker: string;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <p className="eyebrow">{kicker}</p>
        <h1 tabIndex={-1}>{title}</h1>
        <p className="muted">{children}</p>
      </div>
      {action}
    </header>
  );
}
export function Pager({
  offset,
  count,
  onChange,
  name,
}: {
  offset: number;
  count: number;
  onChange: (offset: number) => void;
  name: string;
}) {
  return (
    <nav className="pager" aria-label={`${name} sayfalama`}>
      <span>
        Sayfa {offset / 10 + 1} · Bu sayfada {count} kayıt
      </span>
      <div className="actions">
        <button
          className="secondary"
          disabled={offset === 0}
          onClick={() => onChange(Math.max(0, offset - 10))}
        >
          Önceki
        </button>
        <button className="secondary" disabled={count < 10} onClick={() => onChange(offset + 10)}>
          Sonraki
        </button>
      </div>
    </nav>
  );
}
export function Stat({
  title,
  value,
  detail,
}: {
  title: string;
  value: ReactNode;
  detail: string;
}) {
  return (
    <div className="stat">
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
