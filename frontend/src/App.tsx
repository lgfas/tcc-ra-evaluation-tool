import { useEffect, useState } from 'react';
import { api, ApiError, type User } from './services/api';
import { ChecklistList, ChecklistCreate, ChecklistDetail } from './pages/ChecklistsPage';
import { EvaluationList, EvaluationCreate, EvaluationDetail } from './pages/EvaluationsPage';
import EvaluationRespondPage from './pages/EvaluationRespondPage';
import CatalogPage from './pages/CatalogPage';
import { allowAnswerNavigation } from './services/evaluations';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import Notice from './components/Notice';
import AppLayout from './components/AppLayout';
import { ArchitectureList, ArchitectureCreate, ArchitectureDetail } from './pages/ArchitecturesPage';
export default function App() {
  const [route, setRoute] = useState(window.location.hash.slice(1) || '/');
  const [derivedChecklistId, setDerivedChecklistId] = useState<number | null>(null);
  useEffect(() => {
    let acceptedHash = window.location.hash || '#/';
    const change = () => {
      if (!allowAnswerNavigation()) {
        window.history.replaceState(null, '', acceptedHash);
        return;
      }
      acceptedHash = window.location.hash || '#/';
      setRoute(window.location.hash.slice(1) || '/');
    };
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);
  const [path, query = ''] = route.split('?');
  useEffect(() => {
    if (derivedChecklistId !== null && path === `/checklists/${derivedChecklistId}`) setDerivedChecklistId(null);
  }, [path, derivedChecklistId]);
  const responseRoute = /^\/evaluations\/(\d+)\/respond$/.exec(path);
  const evaluationDetail = /^\/evaluations\/(\d+)$/.exec(path);
  const checklistDetail = /^\/checklists\/(\d+)$/.exec(route);
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
      : path === '/evaluations' ? <EvaluationList />
      : path === '/evaluations/new' ? <EvaluationCreate key={route} initialRaVersionId={Number(new URLSearchParams(query).get('ra_version_id')) || 0} initialChecklistVersionId={Number(new URLSearchParams(query).get('checklist_version_id')) || 0} />
      : path === '/catalog' ? <CatalogPage />
      : responseRoute ? <EvaluationRespondPage key={responseRoute[1]} id={Number(responseRoute[1])} />
      : evaluationDetail ? <EvaluationDetail key={evaluationDetail[1]} id={Number(evaluationDetail[1])} />
      : route === '/checklists' ? <ChecklistList />
      : route === '/checklists/new' ? <ChecklistCreate />
      : checklistDetail ? <ChecklistDetail key={checklistDetail[1]} id={Number(checklistDetail[1])} derivationCreated={derivedChecklistId === Number(checklistDetail[1])} onDerived={id => {setDerivedChecklistId(id); window.location.hash = `/checklists/${id}`;}} />
      : detail ? <ArchitectureDetail key={detail[1]} id={Number(detail[1])} />
      : <section className="card"><h1>Página não encontrada</h1><a href="#/">Voltar ao início</a></section>}
  </AppLayout>;
}
