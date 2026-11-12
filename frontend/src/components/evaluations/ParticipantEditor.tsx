import { useState, type FormEvent } from 'react';
import { evaluationError, type Participant, type EvaluationRole } from '../../services/evaluations';
import EditorPanel from '../EditorPanel';
import Notice from '../Notice';

export default function ParticipantEditor({ initial, roles, onSave, onClose }: {
  initial: Participant | null; roles: EvaluationRole[];
  onSave: (email: string, roleIds: number[]) => Promise<void>; onClose: () => void;
}) {
  const [email, setEmail] = useState('');
  const [selected, setSelected] = useState(initial?.stakeholder_roles.map(role => role.id) ?? []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {await onSave(email, selected);} catch (err) {setError(evaluationError(err));} finally {setBusy(false);}
  }
  return <EditorPanel title={initial ? 'Editar papéis do participante' : 'Adicionar participante'} onClose={onClose} busy={busy}>
    {error && <Notice message={error} error />}
    <form onSubmit={save}><fieldset disabled={busy}>
      {initial ? <div><strong>{initial.user.name}</strong><p className="muted">{initial.user.email}</p></div> : <><label>E-mail do participante<input type="email" required maxLength={254} autoComplete="off" value={email} onChange={event => setEmail(event.target.value)} /></label><small>Informe o e-mail exato de uma conta já cadastrada.</small></>}
      <fieldset className="stakeholder-choices"><legend>Stakeholders da checklist</legend>
        {roles.map(role => <label key={role.id} className="checkbox-row"><input type="checkbox" checked={selected.includes(role.id)} onChange={event => setSelected(current => event.target.checked ? [...current, role.id] : current.filter(id => id !== role.id))} />{role.name}</label>)}
        {!roles.length && <p className="muted">Esta versão não possui stakeholders.</p>}
        <small>{selected.length ? `Papéis selecionados: ${roles.filter(role => selected.includes(role.id)).map(role => role.name).join(', ')}.` : 'Sem papéis: somente questões comuns a todos os participantes.'}</small>
      </fieldset>
    </fieldset><div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancelar</button><button disabled={busy}>{busy ? 'Salvando…' : 'Salvar participante'}</button></div></form>
  </EditorPanel>;
}
