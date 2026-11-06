import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import Notice from '../components/Notice';
import RAElements from '../components/RAElements';

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
  return <section className="card"><a href="#/reference-architectures">Voltar à listagem</a><h1>{step === 1 ? 'Nova Arquitetura de Referência' : 'Criar primeira versão'}</h1>
    <p>Etapa {step} de 2. O cadastro será salvo na confirmação final.</p>{error && <Notice message={error} error />}
    <form onSubmit={submit}><fieldset disabled={busy}>{step === 1 ? <Metadata name={name} visibility={visibility} onName={setName} onVisibility={setVisibility} /> : <><p>{name} · {visibility}</p><VersionFields version={version} description={description} onVersion={setVersion} onDescription={setDescription} /></>}</fieldset>
      <div className="actions">{step === 2 && <button type="button" disabled={busy} className="secondary" onClick={() => {setStep(1); setError('');}}>Voltar</button>}<button disabled={busy}>{busy ? 'Salvando…' : step === 1 ? 'Continuar' : 'Confirmar criação'}</button></div></form></section>;
}
export function ArchitectureList() {
  const [items, setItems] = useState<Architecture[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function load() { setLoading(true); setError(''); try {setItems(await api<Architecture[]>(base));} catch (err) {setError(message(err));} finally {setLoading(false);} }
  useEffect(() => {void load();}, []);
  return <section className="card"><h1>Minhas Arquiteturas de Referência</h1><a className="button-link" href="#/reference-architectures/new">Criar Arquitetura de Referência</a>
    {loading ? <p role="status">Carregando arquiteturas…</p> : error ? <><Notice message={error} error /><button onClick={load}>Tentar novamente</button></> : items.length === 0 ? <p>Você ainda não possui Arquiteturas de Referência. Crie sua primeira RA para começar.</p> : <ul className="ra-list">{items.map(item => <li key={item.id}><h2><a href={`#/reference-architectures/${item.id}`}>{item.name}</a></h2><p>{item.visibility} · {item.role} · {item.version_count} versão(ões)</p></li>)}</ul>}</section>;
}
export function ArchitectureDetail({id}: {id: number}) {
  const [architecture, setArchitecture] = useState<Architecture | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
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
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(''); setSuccess('');
    try {
      if (mode === 'metadata') {
        const result = await api<Architecture>(`${base}${id}/`, 'PATCH', {name, visibility}); setArchitecture(result);
        setSuccess('Dados da arquitetura atualizados.');
      } else {
        const result = await api<Version>(`${base}${id}/versions/`, 'POST', {version, description_markdown: description});
        await load(); setSelected(result.id); setVersion(''); setDescription(''); setSuccess('Nova versão criada.');
      }
      setMode('read');
    } catch (err) {setError(message(err));} finally {setBusy(false);}
  }
  const content = architecture?.versions.find(v => v.id === selected);
  return <section className="card"><a href="#/reference-architectures">Voltar à listagem</a>{error && <Notice message={error} error />}{success && <Notice message={success} />}
    {loading ? <p role="status">Carregando arquitetura…</p> : !architecture ? <button onClick={load}>Tentar novamente</button> : <><h1>{architecture.name}</h1><p>{architecture.visibility}{architecture.role && ` · ${architecture.role}`}</p>
      {mode === 'read' ? <><div className="actions">{architecture.role === 'OWNER' && <button onClick={() => {setName(architecture.name); setVisibility(architecture.visibility); setMode('metadata'); setError(''); setSuccess('');}}>Alterar nome/visibilidade</button>}{architecture.role && <button onClick={() => {setMode('version'); setError(''); setSuccess('');}}>Criar nova versão</button>}</div>
        <h2>Versões</h2><label>Versão selecionada<select value={selected ?? ''} onChange={e => setSelected(Number(e.target.value))}>{architecture.versions.map(v => <option key={v.id} value={v.id}>{v.version} — {new Date(v.created_at).toLocaleString('pt-BR')}</option>)}</select></label>
        {content && <article><h2>Versão {content.version}</h2><p>Criada em {new Date(content.created_at).toLocaleString('pt-BR')}</p><pre className="markdown-text">{content.description_markdown}</pre><RAElements key={content.id} architectureId={id} versionId={content.id} canEdit={architecture.role === 'OWNER' || architecture.role === 'EDITOR'} /></article>}</> : <form onSubmit={submit}><h2>{mode === 'metadata' ? 'Alterar dados da RA' : 'Criar nova versão'}</h2><fieldset disabled={busy}>{mode === 'metadata' ? <Metadata name={name} visibility={visibility} onName={setName} onVisibility={setVisibility} /> : <VersionFields version={version} description={description} onVersion={setVersion} onDescription={setDescription} />}</fieldset><div className="actions"><button disabled={busy}>Salvar</button><button type="button" className="secondary" disabled={busy} onClick={() => {setMode('read'); setError('');}}>Cancelar</button></div></form>}</>}
  </section>;
}
