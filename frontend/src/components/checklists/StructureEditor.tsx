import { useId, useState, type FormEvent } from 'react';
import EditorPanel from '../EditorPanel';
import Notice from '../Notice';
import { checklistError } from '../../services/checklists';

export default function StructureEditor({ kind, initial, onSave, onClose }: {
  kind: 'section' | 'stakeholder'; initial: {name: string; description?: string} | null;
  onSave: (data: {name: string; description?: string}) => Promise<void>; onClose: () => void;
}) {
  const descriptionId = useId();
  const [name, setName] = useState(initial?.name ?? '');
  const [description, setDescription] = useState(initial?.description ?? '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { await onSave({name, ...(kind === 'stakeholder' ? {description} : {})}); }
    catch (err) {setError(checklistError(err));} finally {setBusy(false);}
  }
  const title = kind === 'section' ? (initial ? 'Editar seção' : 'Adicionar seção') : (initial ? 'Editar stakeholder' : 'Adicionar stakeholder');
  return <EditorPanel title={title} onClose={onClose} busy={busy}>{error && <Notice message={error} error />}
    <form onSubmit={save}><fieldset disabled={busy}>
      <label>Nome<input required maxLength={255} value={name} onChange={event => setName(event.target.value)} /></label>
      {kind === 'stakeholder' && <label><span id={descriptionId}>Descrição</span><textarea aria-labelledby={descriptionId} rows={4} value={description} onChange={event => setDescription(event.target.value)} /></label>}
    </fieldset><div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancelar</button><button disabled={busy}>{busy ? 'Salvando…' : 'Salvar'}</button></div></form>
  </EditorPanel>;
}
