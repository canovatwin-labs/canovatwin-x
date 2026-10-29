import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ApiClient } from './api/client';
import type { Principal, Schema } from './api/types';
import { Empty, ErrorNotice } from './components';
import { useRoute } from './hooks';
import { IncidentList, NewAnalysis, AgentCatalog } from './pages';
import { IncidentDetail } from './IncidentDetail';

export type Session = { api: ApiClient; principal: Principal; health: Schema['Readiness'] };

export function App() {
  const [session, setSession] = useState<Session>();
  const [expired, setExpired] = useState(false);
  const current = useRef<ApiClient | undefined>(undefined);
  const route = useRoute();
  const logout = () => {
    current.current?.close();
    current.current = undefined;
    setSession(undefined);
  };
  useEffect(() => () => current.current?.close(), []);
  const connect = (next: Session) => {
    current.current = next.api;
    setExpired(false);
    setSession(next);
  };
  const unauthorized = () => {
    logout();
    setExpired(true);
  };
  useEffect(() => {
    if (session) document.querySelector<HTMLHeadingElement>('main h1')?.focus();
  }, [route, session]);
  if (!session)
    return <Login onConnect={connect} onUnauthorized={unauthorized} expired={expired} />;
  const incident = /^\/incidents\/([A-Za-z0-9_-]{1,100})$/.exec(route)?.[1];
  const page =
    route === '/new' ? (
      <NewAnalysis session={session} />
    ) : route === '/agents' ? (
      <AgentCatalog api={session.api} />
    ) : incident ? (
      <IncidentDetail key={incident} session={session} id={incident} />
    ) : route === '/incidents' ? (
      <IncidentList api={session.api} />
    ) : (
      <Empty>
        Bu sayfa bulunamadı. <a href="#/incidents">Olay listesine dön</a>
      </Empty>
    );
  return (
    <div className="app-shell">
      <a
        className="skip"
        href="#main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById('main')?.focus();
        }}
      >
        İçeriğe geç
      </a>
      <aside className="sidebar">
        <a href="#/incidents" className="brand">
          <span className="brand-mark" aria-hidden="true">
            CX
          </span>
          <span>
            CanovaTwin <b>X</b>
            <small>İnceleme paneli</small>
          </span>
        </a>
        <p className="sidebar-caption">ÇALIŞMA ALANI</p>
        <nav aria-label="Ana gezinme">
          <a href="#/incidents" aria-current={route.startsWith('/incidents') ? 'page' : undefined}>
            <span aria-hidden="true">01</span>Olay incelemeleri
          </a>
          <a href="#/new" aria-current={route === '/new' ? 'page' : undefined}>
            <span aria-hidden="true">02</span>Yeni analiz
          </a>
          <a href="#/agents" aria-current={route === '/agents' ? 'page' : undefined}>
            <span aria-hidden="true">03</span>Ajan kataloğu
          </a>
        </nav>
        <div className="sidebar-bottom">
          <span className="mode-label">SİMÜLASYON ORTAMI</span>
          <p>
            Yerel ve çevrimdışı.
            <br />
            Sentetik veri ile çalışıyor.
          </p>
          <small>
            Uygulama {session.health.application_version}
            <br />
            Analiz motoru {session.health.engine_version}
          </small>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className="environment">
            <span className="dot" />
            Yerel çalışma alanı
          </span>
          <div className="actions">
            <span className="role-label">
              {session.principal.role === 'writer' ? 'Okuma + yazma' : 'Salt okunur'}
            </span>
            <button className="secondary" onClick={logout}>
              Oturumu kapat
            </button>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          {page}
        </main>
        <footer>CanovaTwin X · Karar destek pilotu · Sonuçlar insan incelemesi içindir.</footer>
      </div>
    </div>
  );
}

export function Login({
  onConnect,
  onUnauthorized,
  expired,
}: {
  onConnect: (session: Session) => void;
  onUnauthorized: () => void;
  expired: boolean;
}) {
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const attempt = useRef<ApiClient | undefined>(undefined);
  useEffect(
    () => () => {
      attempt.current?.close();
    },
    [],
  );
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setError(undefined);
    setBusy(true);
    const api = new ApiClient(token.trim(), onUnauthorized);
    attempt.current = api;
    try {
      const [principal, health] = await Promise.all([api.session(), api.health()]);
      if (attempt.current !== api) return;
      attempt.current = undefined;
      setToken('');
      onConnect({ api, principal, health });
    } catch (issue) {
      if (attempt.current === api) {
        api.close();
        attempt.current = undefined;
        setError(issue);
        setBusy(false);
      }
    }
  }
  return (
    <div className="login-page">
      <div className="login-story">
        <p className="eyebrow">CANOVATWIN X / YEREL PİLOT</p>
        <h1>
          Ölçümden
          <br />
          <span>kanıta.</span>
        </h1>
        <p>
          Veri merkezi soğutmasını inceleyin.
          <br />
          Aday nedenleri, kaynakları ve ajanların izini tek yerde görün.
        </p>
        <div className="login-facts">
          <span>36 kayıtlı rol</span>
          <span>12 uygulanmış uzman</span>
          <span>0 LLM çağrısı</span>
        </div>
        <small>Sentetik telemetri · Fiziksel kontrol komutu yok</small>
      </div>
      <section className="login-card" aria-labelledby="login-title">
        <span className="brand-mark" aria-hidden="true">
          CX
        </span>
        <p className="eyebrow">İNCELEME PANELİ</p>
        <h2 id="login-title">Çalışma alanına bağlanın</h2>
        <p className="muted">Yerel yapılandırmanızdaki okuma veya yazma anahtarını kullanın.</p>
        {expired && (
          <p className="notice warn" role="status">
            Oturum sona erdi. Yeniden bağlantı kurun.
          </p>
        )}
        {error !== undefined && <ErrorNotice error={error} />}
        <form onSubmit={submit}>
          <label htmlFor="access-key">Erişim anahtarı</label>
          <input
            id="access-key"
            type="password"
            autoComplete="current-password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            required
            minLength={32}
            maxLength={256}
            disabled={busy}
            aria-describedby="key-help"
          />
          <p id="key-help" className="hint">
            Anahtar bu sekmenin belleğinde kalır. Sayfayı yenilemek veya oturumu kapatmak erişimi
            temizler.
          </p>
          <button className="primary wide" disabled={busy || !token.trim()}>
            {busy ? 'Bağlantı kuruluyor…' : 'Çalışma alanını aç'}
          </button>
        </form>
        <details className="help">
          <summary>Anahtar nerede?</summary>
          <p>
            Proje klasöründeki <code>.local/api-config.json</code> dosyasında{' '}
            <code>read_token</code> veya <code>write_token</code> alanını kullanın. İlk kurulum için
            kullanım rehberindeki API başlatma adımlarını izleyin. Anahtarı sohbet mesajına
            yapıştırmayın.
          </p>
        </details>
      </section>
    </div>
  );
}
