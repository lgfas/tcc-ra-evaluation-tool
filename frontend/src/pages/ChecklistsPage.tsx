import { useEffect, useId, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import { checklistBase as base, checklistError, type Checklist, type ChecklistSummary, type ChecklistVersion } from '../services/checklists';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import EditorPanel from '../components/EditorPanel';
import Notice from '../components/Notice';
import ChecklistStructure from '../components/checklists/ChecklistStructure';

type Metadata = Pick<Checklist, 'name' | 'origin' | 'visibility'>;
function MetadataFields({ value, onChange }: {value: Metadata; onChange: (next: Metadata) => void}) {
  const fieldId = useId();
  return <>
    <label>Nome<input required maxLength={255} value={value.name} onChange={event => onChange({...value, name:event.target.value})} /></label>
    <label><span id={`${fieldId}-origin`}>Origem ou fonte</span><textarea aria-labelledby={`${fieldId}-origin`} rows={3} value={value.origin} onChange={event => onChange({...value, origin:event.target.value})} /></label>
    <small>Opcional. Registre a fonte quando a checklist for baseada ou adaptada de outro instrumento.</small>
    <label><span id={`${fieldId}-visibility`}>Visibilidade</span><select aria-labelledby={`${fieldId}-visibility`} value={value.visibility} onChange={event => onChange({...value, visibility:event.target.value as Metadata['visibility']})}><option value="PRIVATE">Privada</option><option value="PUBLIC">Pública</option></select></label>
  </>;
}
export function ChecklistList() {
  const [items, setItems] = useState<ChecklistSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<ChecklistSummary[]>(base).then(data => {if (active) setItems(data);})
      .catch(err => {if (active) setError(checklistError(err));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [retry]);
  return <section className="page-stack"><PageHeader title="Minhas Checklists" eyebrow="Checklists" actions={<a className="button-link" href="#/checklists/new">+ Nova checklist</a>} />
    {loading ? <p role="status">Carregando checklists…</p> : error ? <><Notice message={error} error /><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></> : items.length ? <ul className="architecture-grid">
      {items.map(item => <li className="card" key={item.id}><span className="badge">{item.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</span><h2><a href={`#/checklists/${item.id}`}>{item.name}</a></h2>
        <p className="muted preserve-lines">Origem: {item.origin || 'Não informada'}</p><p className="muted">{item.version_count} versão(ões)</p><a href={`#/checklists/${item.id}`}>Abrir checklist →</a></li>)}
    </ul> : <div className="card"><EmptyState title="Nenhuma checklist cadastrada"><p>Crie seu primeiro instrumento de avaliação.</p><a href="#/checklists/new">Criar checklist</a></EmptyState></div>}
  </section>;
}
export function ChecklistCreate() {
  const [metadata, setMetadata] = useState<Metadata>({name:'', origin:'', visibility:'PRIVATE'});
  const [version, setVersion] = useState('');
  const [step, setStep] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setError('');
    if (step === 1) {setStep(2); return;}
    setBusy(true);
    try {
      const result = await api<Checklist>(base, 'POST', {...metadata, initial_version:{version}});
      window.location.hash = `/checklists/${result.id}`;
    } catch (err) {setError(checklistError(err));} finally {setBusy(false);}
  }
  return <section className="page-stack form-page"><PageHeader title={step === 1 ? 'Nova checklist' : 'Criar primeira versão'} eyebrow={<a href="#/checklists">← Minhas Checklists</a>} />
    <div className="card"><p>Etapa {step} de 2. A checklist será salva somente na confirmação final.</p>{error && <Notice message={error} error />}
      <form onSubmit={save}><fieldset disabled={busy}>{step === 1 ? <MetadataFields value={metadata} onChange={setMetadata} /> : <><p>{metadata.name} · {metadata.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</p>
        <label>Identificador da versão<input required maxLength={100} value={version} onChange={event => setVersion(event.target.value)} /></label></>}</fieldset>
        <div className="actions form-actions">{step === 2 && <button type="button" className="secondary" disabled={busy} onClick={() => {setStep(1); setError('');}}>Voltar</button>}
          <button disabled={busy}>{busy ? 'Salvando…' : step === 1 ? 'Continuar' : 'Confirmar criação'}</button></div>
      </form></div>
  </section>;
}
function MetadataEditor({ checklist, onSaved, onClose }: {checklist: Checklist; onSaved: (next: Checklist) => void; onClose: () => void}) {
  const [value, setValue] = useState<Metadata>({name:checklist.name, origin:checklist.origin, visibility:checklist.visibility});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {onSaved(await api<Checklist>(`${base}${checklist.id}/`, 'PATCH', value));}
    catch (err) {setError(checklistError(err));} finally {setBusy(false);}
  }
  return <EditorPanel title="Alterar dados da checklist" onClose={onClose} busy={busy}>{error && <Notice message={error} error />}
    <form onSubmit={save}><fieldset disabled={busy}><MetadataFields value={value} onChange={setValue} /></fieldset><div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancelar</button><button disabled={busy}>{busy ? 'Salvando…' : 'Salvar'}</button></div></form>
  </EditorPanel>;
}
function VersionEditor({ checklist, onSaved, onClose }: {checklist: Checklist; onSaved: (version: ChecklistVersion) => void; onClose: () => void}) {
  const [version, setVersion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {onSaved(await api<ChecklistVersion>(`${base}${checklist.id}/versions/`, 'POST', {version}));}
    catch (err) {setError(checklistError(err));} finally {setBusy(false);}
  }
  return <EditorPanel title="Criar nova versão" onClose={onClose} busy={busy}>{error && <Notice message={error} error />}
    <form onSubmit={save}><p className="muted">A nova versão começará vazia. O conteúdo das versões anteriores será mantido.</p><fieldset disabled={busy}>
      <label>Identificador da versão<input required maxLength={100} value={version} onChange={event => setVersion(event.target.value)} /></label></fieldset>
      <div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancelar</button><button disabled={busy}>{busy ? 'Salvando…' : 'Criar versão'}</button></div></form>
  </EditorPanel>;
}
export function ChecklistDetail({ id }: {id: number}) {
  const [checklist, setChecklist] = useState<Checklist | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [retry, setRetry] = useState(0);
  const [editor, setEditor] = useState<'metadata' | 'version' | null>(null);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<Checklist>(`${base}${id}/`).then(item => {if (active) {setChecklist(item); setSelected(item.versions[0]?.id ?? null);}})
      .catch(err => {if (active) setError(checklistError(err));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [id, retry]);
  if (loading) return <p role="status">Carregando checklist…</p>;
  if (!checklist || error) return <section className="page-stack"><PageHeader title="Checklist indisponível" /><Notice message={error || 'Não foi possível carregar a checklist.'} error /><a href="#/checklists">Voltar à listagem</a><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></section>;
  return <section className="page-stack checklist-page"><PageHeader title={checklist.name} eyebrow={<a href="#/checklists">Checklist</a>}
    badge={<span className="badge">{checklist.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</span>}
    actions={checklist.can_edit ? <><button className="secondary" onClick={() => {setEditor('metadata'); setSuccess('');}}>Alterar dados</button><button onClick={() => {setEditor('version'); setSuccess('');}}>+ Nova versão</button></> : undefined} />
    <div className="metadata-row"><label className="version-selector"><span className="sr-only">Versão selecionada</span><select value={selected ?? ''} onChange={event => {setSelected(Number(event.target.value)); setSuccess('');}}>
      {checklist.versions.map(version => <option key={version.id} value={version.id}>Versão {version.version}</option>)}</select></label><p className="muted checklist-origin">Origem: {checklist.origin || 'Não informada'}</p></div>
    {!checklist.can_edit && <p className="muted">Consulta pública · Somente leitura</p>}{success && <Notice message={success} />}
    {selected !== null ? <ChecklistStructure key={selected} path={`${base}${id}/versions/${selected}/`} canEdit={checklist.can_edit} /> : <EmptyState title="Nenhuma versão disponível" />}
    {checklist.can_edit && editor === 'metadata' && <MetadataEditor checklist={checklist} onClose={() => setEditor(null)} onSaved={next => {setChecklist(next); setEditor(null); setSuccess('Dados da checklist atualizados.');}} />}
    {checklist.can_edit && editor === 'version' && <VersionEditor checklist={checklist} onClose={() => setEditor(null)} onSaved={version => {
      setChecklist(current => current ? {...current, versions:[version, ...current.versions], version_count:current.version_count + 1} : current);
      setSelected(version.id); setEditor(null); setSuccess('Nova versão criada.');
    }} />}
  </section>;
}
