import { useId, useState, type FormEvent } from 'react';
import EditorPanel from '../EditorPanel';
import Notice from '../Notice';
import MoveControls, { moveItem } from './MoveControls';
import { checklistError, type Question, type QuestionInput, type ChecklistSection, type StakeholderRole } from '../../services/checklists';

export default function QuestionEditor({ initial, sections, stakeholders, onSave, onClose }: {
  initial: Question | null; sections: ChecklistSection[]; stakeholders: StakeholderRole[];
  onSave: (data: QuestionInput) => Promise<void>; onClose: () => void;
}) {
  const fieldId = useId();
  const [statement, setStatement] = useState(initial?.statement ?? '');
  const [responseType, setResponseType] = useState<Question['response_type']>(initial?.response_type ?? 'SINGLE_CHOICE');
  const [commentMode, setCommentMode] = useState<Question['comment_mode']>(initial?.comment_mode ?? 'OPTIONAL');
  const [sectionId, setSectionId] = useState(initial?.section ? String(initial.section.id) : '');
  const [roleIds, setRoleIds] = useState(initial?.stakeholders.map(role => role.id) ?? []);
  // Stable local keys keep keyboard focus on the option when moving it.
  const [options, setOptions] = useState(initial?.options.length
    ? initial.options.map(option => ({key: crypto.randomUUID(), label: option.label}))
    : [{key: crypto.randomUUID(), label: ''}]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      await onSave({statement, response_type: responseType, comment_mode: commentMode,
        section_id: sectionId ? Number(sectionId) : null, stakeholder_ids: roleIds,
        options: responseType === 'TEXT' ? [] : options.map((option, index) => ({label: option.label, order_index: index}))});
    } catch (err) { setError(checklistError(err)); } finally { setBusy(false); }
  }
  return <EditorPanel title={initial ? 'Editar questão' : 'Adicionar questão'} onClose={onClose} busy={busy}>
    {error && <Notice message={error} error />}
    <form onSubmit={save} className="question-form"><fieldset disabled={busy}>
      <label><span id={`${fieldId}-statement`}>{"Enunciado"}</span><textarea aria-labelledby={`${fieldId}-statement`} required rows={3} value={statement} onChange={event => setStatement(event.target.value)} placeholder="Digite o enunciado da questão…" /></label>
      <label><span id={`${fieldId}-response-type`}>{"Tipo de resposta"}</span><select aria-labelledby={`${fieldId}-response-type`} value={responseType} onChange={event => setResponseType(event.target.value as Question['response_type'])}>
        <option value="SINGLE_CHOICE">Seleção única (SINGLE_CHOICE)</option><option value="TEXT">Texto (TEXT)</option></select></label>
      <label><span id={`${fieldId}-comment-mode`}>{"Comentários"}</span><select aria-labelledby={`${fieldId}-comment-mode`} value={commentMode} onChange={event => setCommentMode(event.target.value as Question['comment_mode'])}>
        <option value="NONE">Sem comentário</option><option value="OPTIONAL">Opcional</option><option value="REQUIRED">Obrigatório ao responder</option></select></label>
      {commentMode === 'REQUIRED' && <small>O comentário será exigido na futura avaliação, não durante o cadastro da questão.</small>}
      <label><span id={`${fieldId}-section`}>{"Seção"}</span><select aria-labelledby={`${fieldId}-section`} value={sectionId} onChange={event => setSectionId(event.target.value)}><option value="">Sem seção</option>
        {sections.map(section => <option value={section.id} key={section.id}>{section.name}</option>)}</select></label>
      {responseType === 'SINGLE_CHOICE' && <fieldset className="options-editor"><legend>Opções de resposta</legend>
        <ol>{options.map((option, index) => <li key={option.key}>
          <label><span className="sr-only">Opção {index + 1}</span><input required maxLength={255} value={option.label} onChange={event => setOptions(current => current.map(item => item.key === option.key ? {...item, label: event.target.value} : item))} /></label>
          <div className="actions"><MoveControls label={`opção ${index + 1}`} index={index} count={options.length} onMove={direction => setOptions(current => moveItem(current, index, direction))} />
            <button type="button" className="secondary" disabled={options.length === 1} aria-label={`Remover opção ${index + 1}`} onClick={() => setOptions(current => current.filter(item => item.key !== option.key))}>×</button></div>
        </li>)}</ol><button type="button" className="secondary" onClick={() => setOptions(current => [...current, {key: crypto.randomUUID(), label: ''}])}>+ Adicionar opção</button>
      </fieldset>}
      <fieldset className="stakeholder-choices"><legend>Stakeholders</legend>
        {stakeholders.map(role => <label className="checkbox-row" key={role.id}><input type="checkbox" checked={roleIds.includes(role.id)} onChange={event => setRoleIds(current => event.target.checked ? [...current, role.id] : current.filter(id => id !== role.id))} />{role.name}</label>)}
        <small>{stakeholders.length ? 'Sem seleção: questão comum a todos os participantes. Com vários papéis: qualquer um deles será suficiente.' : 'Nenhum stakeholder cadastrado. Sem associação, a questão será comum a todos os participantes.'}</small>
      </fieldset>
    </fieldset><div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancelar</button><button disabled={busy}>{busy ? 'Salvando…' : 'Salvar questão'}</button></div></form>
  </EditorPanel>;
}
