import { useEffect, useId, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';

type ArtifactType = 'ra' | 'checklist';
interface CatalogItem {id: number; name: string; visibility: 'PUBLIC'; version_count: number; origin?: string}
export default function CatalogPage() {
  const [type, setType] = useState<ArtifactType>('ra');
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const searchId = useId();
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    const params = new URLSearchParams({type, q:query});
    api<CatalogItem[]>(`/catalog/?${params}`).then(result => {if (active) setItems(result);})
      .catch(err => {if (active) setError(err instanceof Error ? err.message : 'Não foi possível consultar o catálogo.');})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [type, query, retry]);
  function search(event: FormEvent) {
    event.preventDefault(); setLoading(true); setQuery(input.trim()); setRetry(value => value + 1);
  }
  return <section className="page-stack"><PageHeader title="Catálogo" eyebrow="Artefatos públicos" />
    <p className="muted">Consulte versões públicas e utilize-as em avaliações. A reutilização preserva o artefato original e suas permissões.</p>
    <nav className="tabs" aria-label="Tipos de artefatos do catálogo">
      <button className={type === 'ra' ? 'is-active' : ''} aria-pressed={type === 'ra'} onClick={() => {if (type !== 'ra') {setLoading(true); setType('ra');}}}>Arquiteturas de Referência</button>
      <button className={type === 'checklist' ? 'is-active' : ''} aria-pressed={type === 'checklist'} onClick={() => {if (type !== 'checklist') {setLoading(true); setType('checklist');}}}>Checklists</button>
    </nav>
    <form className="catalog-search" role="search" aria-label="Pesquisar artefatos públicos" onSubmit={search}>
      <label htmlFor={searchId}>Buscar por nome<input id={searchId} type="search" maxLength={255} value={input} onChange={event => setInput(event.target.value)} placeholder="Informe parte do nome" /></label>
      <button type="submit">Buscar</button>
    </form>
    {loading ? <p role="status">Consultando catálogo…</p> : error ? <><Notice message={error} error /><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></> : <>
      <p role="status" className="muted">{items.length} {items.length === 1 ? 'artefato público encontrado' : 'artefatos públicos encontrados'}{query && ` para “${query}”`}.</p>
      {items.length ? <ul className="architecture-grid">{items.map(item => <li key={item.id} className="card catalog-card"><span className="badge">Pública</span><h2>{item.name}</h2>
        {type === 'checklist' && <p className="preserve-lines">Origem: {item.origin || 'Não informada'}</p>}
        <p className="muted">{item.version_count} {item.version_count === 1 ? 'versão' : 'versões'}</p>
        <a href={`#/${type === 'ra' ? 'reference-architectures' : 'checklists'}/${item.id}`} aria-label={`Ver detalhes de ${item.name}`}>Ver detalhes →</a>
      </li>)}</ul> : <div className="card"><EmptyState title="Nenhum artefato público encontrado"><p>{query ? 'Tente outro nome ou limpe a busca para consultar todos os artefatos deste tipo.' : 'Ainda não há artefatos públicos deste tipo no catálogo.'}</p>{query && <button className="secondary" onClick={() => {setInput(''); setQuery('');}}>Limpar busca</button>}</EmptyState></div>}
    </>}
  </section>;
}
