import { useState } from 'react';
import { api, ApiError, type User } from '../services/api';
import Notice from '../components/Notice';
export default function HomePage({ user, onLogout }: {user: User; onLogout: () => void}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function exit() {
    setBusy(true); setError('');
    try { await api('/auth/logout/', 'POST'); onLogout(); }
    catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        try { await api('/auth/me/'); } catch (check) {
          if (check instanceof ApiError && check.status === 403) { onLogout(); return; }
        }
      }
      setError(err instanceof Error ? err.message : 'Não foi possível sair.');
    } finally { setBusy(false); }
  }
  return <section className="card"><p className="eyebrow">Início</p><h1>Olá, {user.name}</h1>
    <p className="identity">{user.email}</p><p>Bem-vindo à ferramenta de apoio à avaliação de Arquiteturas de Referência.</p>
    <p><a href="#/reference-architectures">Abrir Arquiteturas de Referência</a></p><p>Este é o espaço inicial da sua conta. As funcionalidades de avaliação serão disponibilizadas nas próximas etapas do projeto.</p>
    {error && <Notice message={error} error />}<button disabled={busy} onClick={exit}>{busy ? 'Encerrando…' : 'Encerrar sessão'}</button></section>;
}
