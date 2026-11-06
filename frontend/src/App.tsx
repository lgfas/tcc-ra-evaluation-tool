import { useEffect, useState } from 'react';
import { api, ApiError, type User } from './services/api';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import Notice from './components/Notice';
import AppLayout from './components/AppLayout';
import { ArchitectureList, ArchitectureCreate, ArchitectureDetail } from './pages/ArchitecturesPage';
export default function App() {
  const [route, setRoute] = useState(window.location.hash.slice(1) || '/');
  useEffect(() => { const change = () => setRoute(window.location.hash.slice(1) || '/'); window.addEventListener('hashchange', change); return () => window.removeEventListener('hashchange', change); }, []);
  const detail = /^\/reference-architectures\/(\d+)$/.exec(route);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function restore() {
    setLoading(true); setError('');
    try { setUser(await api<User>('/auth/me/')); }
    catch (err) { if (!(err instanceof ApiError && err.status === 403)) setError(err instanceof Error ? err.message : 'Não foi possível recuperar sua sessão.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void restore(); }, []);
  if (loading) return <main className="session-state"><p role="status">Carregando sua sessão…</p></main>;
  if (error) return <main className="session-state"><Notice message={error} error /><button onClick={restore}>Tentar novamente</button></main>;
  if (!user) return <AuthPage onLogin={setUser} />;
  return <AppLayout user={user} route={route} onLogout={() => {setUser(null); window.location.hash = '/';}}>
    {route === '/' ? <HomePage user={user} />
      : route === '/reference-architectures' ? <ArchitectureList />
      : route === '/reference-architectures/new' ? <ArchitectureCreate />
      : detail ? <ArchitectureDetail key={detail[1]} id={Number(detail[1])} />
      : <section className="card"><h1>Página não encontrada</h1><a href="#/">Voltar ao início</a></section>}
  </AppLayout>;
}
