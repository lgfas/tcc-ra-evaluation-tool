import { useEffect, useState } from 'react';
import { statusLabels, type EvaluationSummary } from '../services/evaluations';
import type { ChecklistSummary } from '../services/checklists';
import { api, type User } from '../services/api';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import StatCard from '../components/StatCard';

interface ArchitectureSummary { id: number; name: string; version_count: number }
export default function HomePage({ user }: {user: User}) {
  const [evaluations, setEvaluations] = useState<EvaluationSummary[]>([]);
  const [checklists, setChecklists] = useState<ChecklistSummary[]>([]);
  const [items, setItems] = useState<ArchitectureSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    Promise.all([api<ArchitectureSummary[]>('/reference-architectures/'), api<ChecklistSummary[]>('/checklists/'), api<EvaluationSummary[]>('/checklist-evaluations/')])
      .then(([data, instruments, related]) => { if (active) {setItems(data); setChecklists(instruments); setEvaluations(related);} })
      .catch(err => { if (active) setError(err instanceof Error ? err.message : 'Não foi possível carregar o início.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [retry]);
  return <div className="page-stack">
    <PageHeader title="Início" eyebrow={`Olá, ${user.name}`} actions={<a className="button-link" href="#/reference-architectures/new">+ Nova arquitetura</a>} />
    <p className="muted">Organize suas Arquiteturas de Referência e consulte suas versões e elementos.</p>
    {loading ? <p role="status">Carregando suas arquiteturas…</p> : error ? <><Notice message={error} error /><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></> : <>
      <div className="stats-grid"><StatCard value={items.length} label="Minhas arquiteturas" />
        <StatCard value={items.reduce((total, item) => total + item.version_count, 0)} label="Versões cadastradas" />
        <StatCard label="Minhas checklists" value={checklists.length} /><StatCard label="Minhas avaliações" value={evaluations.length} /></div>
      <div className="panel-grid"><section className="card"><div className="section-heading"><h2>Minhas Arquiteturas de Referência</h2><a href="#/reference-architectures">Ver todas</a></div>
        {items.length ? <ul className="compact-list">{items.slice(0, 5).map(item => <li key={item.id}><a href={`#/reference-architectures/${item.id}`}>{item.name}</a><small>{item.version_count} versão(ões)</small></li>)}</ul>
          : <EmptyState title="Nenhuma arquitetura cadastrada"><p>Crie sua primeira RA para começar.</p><a href="#/reference-architectures/new">Criar Arquitetura de Referência</a></EmptyState>}
      </section><section className="card"><div className="section-heading"><h2>Avaliações por checklist</h2><a href="#/evaluations">Ver todas</a></div>
        {evaluations.length ? <ul className="compact-list">{evaluations.slice(0, 5).map(item => <li key={item.id}><a href={`#/evaluations/${item.id}`}>{item.ra_version.architecture_name} · v{item.ra_version.version}</a><small>{statusLabels[item.status]}</small></li>)}</ul>
          : <EmptyState title="Nenhuma avaliação relacionada"><a href="#/evaluations/new">Criar avaliação</a></EmptyState>}</section></div>
    </>}
  </div>;
}
