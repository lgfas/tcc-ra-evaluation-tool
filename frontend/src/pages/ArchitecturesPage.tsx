import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import Notice from '../components/Notice';
import RAElements from '../components/RAElements';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import StatCard from '../components/StatCard';
import EditorPanel from '../components/EditorPanel';

type Visibility = 'PRIVATE' | 'PUBLIC';
interface Version { id: number; version: string; description_markdown: string; created_at: string }
interface Architecture { id: number; name: string; visibility: Visibility; role: 'OWNER' | 'EDITOR' | null; version_count: number; versions: Version[] }
const base = '/reference-architectures/';
const message = (error: unknown) => error instanceof Error ? error.message : 'Não foi possível concluir a operação.';
function Metadata({name, visibility, onName, onVisibility}: {name: string; visibility: Visibility; onName: (s: string) => void; onVisibility: (s: Visibility) => void}) {
  return <><label>Nome<input required maxLength={255} value={name} onChange={e => onName(e.target.value)} /></label>
    <label>Visibilidade<select value={visibility} onChange={e => onVisibility(e.target.value as Visibility)}><option value="PRIVATE">Privada (PRIVATE)</option><option value="PUBLIC">Pública (PUBLIC)</option></select></label></>;
}
function VersionFields({version, description, onVersion, onDescription}: {version: string; description: string; onVersion: (s: string) => void; onDescription: (s: string) => void}) {
  return <><label>Identificador da versão<input required maxLength={100} value={version} onChange={e => onVersion(e.target.value)} /></label>
    <label>Descrição geral em Markdown<textarea required rows={8} value={description} onChange={e => onDescription(e.target.value)} /></label></>;
}
export function ArchitectureCreate() {
  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [visibility, setVisibility] = useState<Visibility>('PRIVATE');
  const [version, setVersion] = useState('');
  const [description, setDescription] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(e: FormEvent) {
    e.preventDefault(); setError('');
    if (step === 1) { setStep(2); return; }
    setBusy(true);
    try {
      const result = await api<Architecture>(base, 'POST', {name, visibility, initial_version: {version, description_markdown: description}});
      window.location.hash = `/reference-architectures/${result.id}`;
    } catch (err) { setError(message(err)); } finally { setBusy(false); }
  }
  return <section className="page-stack form-page"><PageHeader title={step === 1 ? 'Nova Arquitetura de Referência' : 'Criar primeira versão'} eyebrow={<a href="#/reference-architectures">← Arquiteturas de Referência</a>} /><div className="card">
    <p>Etapa {step} de 2. O cadastro será salvo na confirmação final.</p>{error && <Notice message={error} error />}
    <form onSubmit={submit}><fieldset disabled={busy}>{step === 1 ? <Metadata name={name} visibility={visibility} onName={setName} onVisibility={setVisibility} /> : <><p>{name} · {visibility}</p><VersionFields version={version} description={description} onVersion={setVersion} onDescription={setDescription} /></>}</fieldset>
      <div className="actions">{step === 2 && <button type="button" disabled={busy} className="secondary" onClick={() => {setStep(1); setError('');}}>Voltar</button>}<button disabled={busy}>{busy ? 'Salvando…' : step === 1 ? 'Continuar' : 'Confirmar criação'}</button></div></form></div></section>;
}
export function ArchitectureList() {
  const [items, setItems] = useState<Architecture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function load() { setLoading(true); setError(''); try {setItems(await api<Architecture[]>(base));} catch (err) {setError(message(err));} finally {setLoading(false);} }
  useEffect(() => {void load();}, []);
  return <section className="page-stack"><PageHeader title="Minhas Arquiteturas de Referência" eyebrow="Arquiteturas" actions={<a className="button-link" href="#/reference-architectures/new">+ Nova arquitetura</a>} />
    {loading ? <p role="status">Carregando arquiteturas…</p> : error ? <><Notice message={error} error /><button onClick={load}>Tentar novamente</button></> : items.length === 0 ? <div className="card"><EmptyState title="Nenhuma arquitetura cadastrada"><p>Crie sua primeira RA para começar.</p><a href="#/reference-architectures/new">Criar Arquitetura de Referência</a></EmptyState></div> : <ul className="architecture-grid">{items.map(item => <li className="card" key={item.id}>
      <span className="badge">{item.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</span><h2><a href={`#/reference-architectures/${item.id}`}>{item.name}</a></h2>
      <p className="muted">{item.role === 'OWNER' ? 'Proprietário' : 'Colaborador'} · {item.version_count} versão(ões)</p><a href={`#/reference-architectures/${item.id}`}>Abrir arquitetura →</a></li>)}</ul>}
  </section>;
}
export function ArchitectureDetail({id}: {id: number}) {
  const [architecture, setArchitecture] = useState<Architecture | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'overview' | 'elements'>('overview');
  const [elementCount, setElementCount] = useState<number | undefined>();
  const [mode, setMode] = useState<'read' | 'metadata' | 'version'>('read');
  const [name, setName] = useState('');
  const [visibility, setVisibility] = useState<Visibility>('PRIVATE');
  const [version, setVersion] = useState('');
  const [description, setDescription] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  async function load() {
    setLoading(true); setError('');
    try { const data = await api<Architecture>(`${base}${id}/`); setArchitecture(data); setSelected(current => data.versions.some(v => v.id === current) ? current : data.versions[0]?.id ?? null); }
    catch (err) {setError(message(err));} finally {setLoading(false);}
  }
  useEffect(() => {void load();}, [id]);
  useEffect(() => {
    let active = true;
    setElementCount(undefined);
    if (selected !== null) {
      api<unknown[]>(`${base}${id}/versions/${selected}/elements/`)
        .then(items => { if (active) setElementCount(items.length); })
        .catch(() => { /* The elements area provides an error and retry when opened. */ });
    }
    return () => { active = false; };
  }, [id, selected, tab]);
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(''); setSuccess('');
    try {
      if (mode === 'metadata') {
        const result = await api<Architecture>(`${base}${id}/`, 'PATCH', {name, visibility}); setArchitecture(result);
        setSuccess('Dados da arquitetura atualizados.');
      } else {
        const result = await api<Version>(`${base}${id}/versions/`, 'POST', {version, description_markdown: description});
        setArchitecture(current => current ? {...current, versions: [result, ...current.versions], version_count: current.version_count + 1} : current);
        setSelected(result.id); setVersion(''); setDescription(''); setSuccess('Nova versão criada.');
      }
      setMode('read');
    } catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  const content = architecture?.versions.find(v => v.id === selected);
  function openEditor(next: 'metadata' | 'version') {
    if (!architecture) return;
    setName(architecture.name); setVisibility(architecture.visibility);
    setVersion(''); setDescription(''); setMode(next); setError(''); setSuccess('');
  }
  const canEdit = architecture?.role === 'OWNER' || architecture?.role === 'EDITOR';
  const unavailable = ['Critérios de conformidade', 'Avaliações por checklist', 'Instanciações', 'Conformidade'];
  return <section className="page-stack">
    {error && mode === 'read' && <Notice message={error} error />}{success && <Notice message={success} />}
    {loading ? <p role="status">Carregando arquitetura…</p> : !architecture ? <><PageHeader title="Arquitetura indisponível" /><a href="#/reference-architectures">Voltar à listagem</a><button onClick={load}>Tentar novamente</button></> : <>
      <PageHeader title={architecture.name} eyebrow={<a href="#/reference-architectures">Arquitetura de Referência</a>}
        badge={<span className="badge">{architecture.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</span>}
        actions={<>{architecture.role === 'OWNER' && <button className="secondary" onClick={() => openEditor('metadata')}>Alterar dados da RA</button>}
          {canEdit && <button onClick={() => openEditor('version')}>+ Nova versão</button>}</>} />
      <div className="metadata-row"><label className="version-selector"><span className="sr-only">Versão selecionada</span>
        <select disabled={!architecture.versions.length} value={selected ?? ''} onChange={event => {setSelected(Number(event.target.value)); setSuccess('');}}>
          {architecture.versions.map(item => <option key={item.id} value={item.id}>Versão {item.version}</option>)}
        </select></label><span className="muted">{content && <>Criada em {new Date(content.created_at).toLocaleDateString('pt-BR')} · </>}
          {architecture.role === 'OWNER' ? 'Proprietário' : architecture.role === 'EDITOR' ? 'Colaborador' : 'Consulta pública · Somente leitura'}</span></div>
      <div className="tabs" role="tablist" aria-label="Áreas da arquitetura" onKeyDown={event => {
        if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
          event.preventDefault();
          const next = event.key === 'Home' ? 'overview' : event.key === 'End' ? 'elements' : tab === 'overview' ? 'elements' : 'overview';
          setTab(next); document.getElementById(`tab-${next}`)?.focus();
        }
      }}>
        <button role="tab" id="tab-overview" aria-selected={tab === 'overview'} aria-controls="panel-overview" tabIndex={tab === 'overview' ? 0 : -1} onClick={() => setTab('overview')}>Visão geral</button>
        <button role="tab" id="tab-elements" aria-selected={tab === 'elements'} aria-controls="panel-elements" tabIndex={tab === 'elements' ? 0 : -1} onClick={() => setTab('elements')}>Elementos</button>
        {unavailable.map(label => <button key={label} role="tab" aria-selected={false} disabled title="Ainda não disponível">{label}</button>)}
      </div>
      {!content ? <EmptyState title="Nenhuma versão disponível" /> : <>
        <div role="tabpanel" id="panel-overview" aria-labelledby="tab-overview" hidden={tab !== 'overview'} tabIndex={0} className="page-stack">
          <article className="card"><h2>Descrição</h2><pre className="markdown-text">{content.description_markdown}</pre></article>
          <h2>Resumo</h2><div className="stats-grid"><StatCard label="Elementos" value={elementCount} hint={elementCount === undefined ? 'Consulte a aba Elementos' : undefined} />
            <StatCard label="Avaliações por checklist" hint="Ainda não disponível" /><StatCard label="Instanciações" hint="Ainda não disponível" /><StatCard label="Avaliações de conformidade" hint="Ainda não disponível" /></div>
          <div className="panel-grid"><section className="card"><h2>Avaliações recentes</h2><EmptyState title="Ainda não disponível"><p>As avaliações serão adicionadas em uma próxima etapa.</p></EmptyState></section>
            <section className="card"><h2>Arquiteturas concretas</h2><EmptyState title="Ainda não disponível"><p>As instanciações serão adicionadas em uma próxima etapa.</p></EmptyState></section></div>
        </div>
        <div role="tabpanel" id="panel-elements" aria-labelledby="tab-elements" hidden={tab !== 'elements'} tabIndex={0}>
          {tab === 'elements' && <RAElements key={content.id} architectureId={id} versionId={content.id} canEdit={canEdit} />}
        </div>
      </>}
      {mode !== 'read' && <EditorPanel title={mode === 'metadata' ? 'Alterar dados da RA' : 'Criar nova versão'} busy={busy} onClose={() => {setMode('read'); setError('');}}>
        {error && <Notice message={error} error />}<form onSubmit={submit}><fieldset disabled={busy}>
          {mode === 'metadata' ? <Metadata name={name} visibility={visibility} onName={setName} onVisibility={setVisibility} /> : <VersionFields version={version} description={description} onVersion={setVersion} onDescription={setDescription} />}
        </fieldset><div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={() => {setMode('read'); setError('');}}>Cancelar</button><button disabled={busy}>{busy ? 'Salvando…' : 'Salvar'}</button></div></form>
      </EditorPanel>}
    </>}
  </section>;
}
