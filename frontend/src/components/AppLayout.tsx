import { useEffect, useRef, useState, type ReactNode } from 'react';
import { api, ApiError, type User } from '../services/api';
import Notice from './Notice';
import navDot from '../assets/nav-dot.svg';

const pending = ['Checklists', 'Avaliações', 'Arq. Concretas', 'Catálogo'];
export default function AppLayout({ user, route, onLogout, children }: {
  user: User; route: string; onLogout: () => void; children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const main = useRef<HTMLElement>(null);
  const menu = useRef<HTMLButtonElement>(null);
  const previousRoute = useRef(route);
  useEffect(() => {
    setOpen(false);
    if (previousRoute.current !== route) main.current?.focus();
    previousRoute.current = route;
  }, [route]);
  async function exit() {
    setBusy(true); setError('');
    try { await api('/auth/logout/', 'POST'); onLogout(); }
    catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        try { await api('/auth/me/'); } catch (check) {
          if (check instanceof ApiError && check.status === 403) { onLogout(); return; }
        }
      }
      setError(err instanceof Error ? err.message : 'Não foi possível encerrar a sessão.');
    } finally { setBusy(false); }
  }
  const architectures = route.startsWith('/reference-architectures');
  return <div className="app-layout">
    <a className="skip-link" href="#main-content" onClick={event => {event.preventDefault(); main.current?.focus();}}>Ir para o conteúdo</a>
    <header className="mobile-header"><strong>RA Eval</strong>
      <button ref={menu} className="secondary" aria-expanded={open} aria-controls="app-sidebar" onClick={() => setOpen(!open)} onKeyDown={event => {
        if (event.key === 'Escape') setOpen(false);
      }}>{open ? 'Fechar menu' : 'Abrir menu'}</button>
    </header>
    <aside id="app-sidebar" className={`sidebar ${open ? 'is-open' : ''}`} onKeyDown={event => {
      if (event.key === 'Escape') {setOpen(false); menu.current?.focus();}
    }}>
      <a className="brand" href="#/">RA Eval</a>
      <nav aria-label="Navegação principal" className="sidebar-nav" onClick={event => {
        if (event.target instanceof Element && event.target.closest('a')) {setOpen(false); main.current?.focus();}
      }}>
        <a href="#/" aria-current={route === '/' ? 'page' : undefined}><img src={navDot} alt="" />Início</a>
        <a href="#/reference-architectures" aria-current={architectures ? 'page' : undefined}><img src={navDot} alt="" />Arquiteturas</a>
        {pending.map(label => <span key={label} className="nav-unavailable" aria-disabled="true" title="Ainda não disponível"><img src={navDot} alt="" />{label}<small className="sr-only">Ainda não disponível</small></span>)}
      </nav>
      <div className="sidebar-account"><p className="eyebrow">Conta do usuário</p><strong>{user.name}</strong><span>{user.email}</span>
        <button className="secondary" disabled={busy} onClick={exit}>{busy ? 'Encerrando…' : 'Encerrar sessão'}</button>
      </div>
    </aside>
    <main id="main-content" className="app-main" ref={main} tabIndex={-1}>
      {error && <Notice message={error} error />}{children}
    </main>
  </div>;
}
