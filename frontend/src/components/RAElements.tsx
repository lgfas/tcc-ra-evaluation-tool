import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import Notice from './Notice';
import EditorPanel from './EditorPanel';
import EmptyState from './EmptyState';

interface ElementType { id: number; name: string }
interface Element { id: number; name: string; description_markdown: string; element_type: ElementType }
const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'Não foi possível concluir a operação.';

function ElementForm({ initial, types, onSave, onCancel, onTypeCreated }: {
  initial: Element | null;
  types: ElementType[];
  onSave: (data: { name: string; element_type_id: number; description_markdown: string }) => Promise<void>;
  onCancel: () => void;
  onTypeCreated: (type: ElementType) => void;
}) {
  const [name, setName] = useState(initial?.name ?? '');
  const [description, setDescription] = useState(initial?.description_markdown ?? '');
  const [typeId, setTypeId] = useState(initial ? String(initial.element_type.id) : '');
  const [creatingType, setCreatingType] = useState(false);
  const [typeName, setTypeName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function createType() {
    if (!typeName.trim()) { setError('Informe o nome do novo tipo.'); return; }
    setBusy(true); setError('');
    try {
      const type = await api<ElementType>('/architectural-element-types/', 'POST', {name: typeName});
      onTypeCreated(type); setTypeId(String(type.id)); setCreatingType(false); setTypeName('');
    } catch (err) { setError(errorMessage(err)); } finally { setBusy(false); }
  }
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { await onSave({name, description_markdown: description, element_type_id: Number(typeId)}); }
    catch (err) {setError(errorMessage(err));} finally {setBusy(false);}
  }
  return <EditorPanel title={initial ? 'Editar elemento' : 'Adicionar elemento'} busy={busy} onClose={onCancel}><form onSubmit={save} className="element-form">
    {error && <Notice message={error} error />}
    <fieldset disabled={busy}>
      <label>Nome do elemento<input required maxLength={255} value={name} onChange={e => setName(e.target.value)} /></label>
      <label>Tipo arquitetural<select required value={typeId} onChange={e => setTypeId(e.target.value)}><option value="">Selecione um tipo</option>{types.map(type => <option key={type.id} value={type.id}>{type.name}</option>)}</select></label>
      {!creatingType ? <button className="secondary" type="button" onClick={() => setCreatingType(true)}>+ Criar novo tipo</button> : <div className="type-form">
        <label>Nome do novo tipo<input maxLength={255} value={typeName} onChange={e => setTypeName(e.target.value)} /></label>
        <div className="actions"><button type="button" onClick={createType}>Salvar novo tipo</button><button type="button" className="secondary" onClick={() => setCreatingType(false)}>Cancelar novo tipo</button></div>
      </div>}
      <label>Descrição do elemento em Markdown<textarea required rows={6} value={description} onChange={e => setDescription(e.target.value)} /></label>
    </fieldset>
    <div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button><button disabled={busy || creatingType}>{busy ? 'Salvando…' : 'Salvar elemento'}</button></div>
  </form></EditorPanel>;
}

// Mounted with a version-specific key: changing versions discards this version's form and results.
export default function RAElements({architectureId, versionId, canEdit}: {architectureId: number; versionId: number; canEdit: boolean}) {
  const path = `/reference-architectures/${architectureId}/versions/${versionId}/elements/`;
  const [elements, setElements] = useState<Element[]>([]);
  const [types, setTypes] = useState<ElementType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState<{initial: Element | null} | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    Promise.all([
      api<Element[]>(path),
      canEdit ? api<ElementType[]>(`/architectural-element-types/?reference_architecture_id=${architectureId}`) : Promise.resolve([]),
    ]).then(([items, availableTypes]) => {if (active) {setElements(items); setTypes(availableTypes);}})
      .catch(err => {if (active) setError(errorMessage(err));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [path, architectureId, canEdit, retry]);

  async function save(data: {name: string; element_type_id: number; description_markdown: string}) {
    const initial = form?.initial;
    const result = await api<Element>(initial ? `${path}${initial.id}/` : path, initial ? 'PATCH' : 'POST', data);
    setElements(current => (initial ? current.map(item => item.id === result.id ? result : item) : [...current, result])
      .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR') || a.id - b.id));
    setForm(null); setSuccess(initial ? 'Elemento atualizado.' : 'Elemento cadastrado.');
  }
  function open(initial: Element | null) {setForm({initial}); setSuccess('');}
  return <section aria-labelledby="elements-title" className="elements-section"><div className="section-heading"><div><h2 id="elements-title">Elementos</h2><p className="muted">Elementos arquiteturais desta versão.</p></div>
    {canEdit && !loading && !error && <button disabled={!!form} onClick={() => open(null)}>+ Adicionar elemento</button>}</div>
    {success && <Notice message={success} />}
    {loading ? <p role="status">Carregando elementos…</p> : error ? <><Notice message={error} error /><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></> : <>
      {canEdit && form && <ElementForm key={form.initial?.id ?? 'new'} initial={form.initial} types={types} onSave={save} onCancel={() => setForm(null)} onTypeCreated={type => setTypes(current => [...current, type])} />}
      {elements.length === 0 ? <div className="card"><EmptyState title="Nenhum elemento cadastrado"><p>Esta versão ainda não possui elementos arquiteturais.</p></EmptyState></div> : <ul className="element-list">{elements.map(element => <li key={element.id} className="card">
        <div className="section-heading"><h3>{element.name}</h3><span className="badge">{element.element_type.name}</span></div><pre className="markdown-text">{element.description_markdown}</pre>
        {canEdit && <button disabled={!!form} className="secondary" aria-label={`Editar elemento ${element.name}`} onClick={() => open(element)}>Editar elemento</button>}
      </li>)}</ul>}
    </>}
  </section>;
}
