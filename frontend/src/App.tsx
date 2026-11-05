import { useEffect, useState } from 'react';
import { api, ApiError, type User } from './services/api';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import Notice from './components/Notice';
export default function App() {
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
  return <><header><strong>Avaliação de Arquiteturas de Referência</strong><span>Projeto de TCC</span></header>
    <main>{loading ? <p role="status">Carregando sua sessão…</p> : error ? <section className="card"><Notice message={error} error /><button onClick={restore}>Tentar novamente</button></section>
      : user ? <HomePage user={user} onLogout={() => setUser(null)} /> : <AuthPage onLogin={setUser} />}</main></>;
}
