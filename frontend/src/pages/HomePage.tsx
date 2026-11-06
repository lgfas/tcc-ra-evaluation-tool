import { useEffect, useState } from 'react';
import { api, type User } from '../services/api';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import StatCard from '../components/StatCard';

interface ArchitectureSummary { id: number; name: string; version_count: number }
export default function HomePage({ user }: {user: User}) {
  const [items, setItems] = useState<ArchitectureSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<ArchitectureSummary[]>('/reference-architectures/')
      .then(data => { if (active) setItems(data); })
      .catch(err => { if (active) setError(err instanceof Error ? err.message : 'Não foi possível carregar suas arquiteturas.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [retry]);
  return <div className="page-stack">
    <PageHeader title="Início" eyebrow={`Olá, ${user.name}`} actions={<a className="button-link" href="#/reference-architectures/new">+ Nova arquitetura</a>} />
    <p className="muted">Organize suas Arquiteturas de Referência e consulte suas versões e elementos.</p>
    {loading ? <p role="status">Carregando suas arquiteturas…</p> : error ? <><Notice message={error} error /><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></> : <>
      <div className="stats-grid"><StatCard value={items.length} label="Minhas arquiteturas" />
        <StatCard value={items.reduce((total, item) => total + item.version_count, 0)} label="Versões cadastradas" />
        <StatCard label="Checklists" hint="Ainda não disponível" /><StatCard label="Avaliações" hint="Ainda não disponível" /></div>
      <div className="panel-grid"><section className="card"><div className="section-heading"><h2>Minhas Arquiteturas de Referência</h2><a href="#/reference-architectures">Ver todas</a></div>
        {items.length ? <ul className="compact-list">{items.slice(0, 5).map(item => <li key={item.id}><a href={`#/reference-architectures/${item.id}`}>{item.name}</a><small>{item.version_count} versão(ões)</small></li>)}</ul>
          : <EmptyState title="Nenhuma arquitetura cadastrada"><p>Crie sua primeira RA para começar.</p><a href="#/reference-architectures/new">Criar Arquitetura de Referência</a></EmptyState>}
      </section><section className="card"><h2>Avaliações</h2><EmptyState title="Disponível em uma próxima etapa"><p>As avaliações por checklist e de conformidade ainda não estão disponíveis.</p></EmptyState></section></div>
    </>}
  </div>;
}
