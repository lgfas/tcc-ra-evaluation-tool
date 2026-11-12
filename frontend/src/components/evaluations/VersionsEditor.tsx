import { useState, type FormEvent } from 'react';
import { api } from '../../services/api';
import { evaluationBase, evaluationError, type Evaluation, type VersionSelection } from '../../services/evaluations';
import EditorPanel from '../EditorPanel';
import Notice from '../Notice';
import EvaluationSelection from './EvaluationSelection';

export default function VersionsEditor({ evaluation, onSaved, onClose }: {evaluation: Evaluation; onSaved: (next: Evaluation) => void; onClose: () => void}) {
  const initial = {ra_version_id:evaluation.ra_version.id, checklist_version_id:evaluation.checklist_version.id};
  const [selection, setSelection] = useState<VersionSelection>(initial);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {onSaved(await api<Evaluation>(`${evaluationBase}${evaluation.id}/`, 'PATCH', selection));}
    catch (err) {setError(evaluationError(err));} finally {setBusy(false);}
  }
  return <EditorPanel title="Revisar seleção das versões" busy={busy} onClose={onClose}>
    {error && <Notice message={error} error />}<form onSubmit={save}><p className="muted">Trocar a versão da checklist remove os papéis atribuídos aos participantes. Os participantes serão mantidos.</p>
      <EvaluationSelection initial={initial} onChange={setSelection} onReady={setReady} disabled={busy} />
      <div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancelar</button><button disabled={busy || !ready || !selection.ra_version_id || !selection.checklist_version_id}>{busy ? 'Salvando…' : 'Salvar seleção'}</button></div></form>
  </EditorPanel>;
}
