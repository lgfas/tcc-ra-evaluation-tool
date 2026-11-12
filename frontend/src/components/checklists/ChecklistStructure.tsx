import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { checklistError, commentLabels, type ChecklistSection, type StakeholderRole, type Question, type QuestionInput } from '../../services/checklists';
import EmptyState from '../EmptyState';
import Notice from '../Notice';
import QuestionEditor from './QuestionEditor';
import StructureEditor from './StructureEditor';
import MoveControls, { moveItem } from './MoveControls';

type Tab = 'questions' | 'sections' | 'stakeholders';
type Editor = {kind: 'question'; initial: Question | null}
  | {kind: 'section'; initial: ChecklistSection | null}
  | {kind: 'stakeholder'; initial: StakeholderRole | null};
const tabs: {id: Tab; label: string}[] = [{id:'questions', label:'Questões'}, {id:'sections', label:'Seções'}, {id:'stakeholders', label:'Stakeholders'}];

// A version-specific key in ChecklistDetail resets every result and editor on version changes.
export default function ChecklistStructure({ path, canEdit }: {path: string; canEdit: boolean}) {
  const [sections, setSections] = useState<ChecklistSection[]>([]);
  const [stakeholders, setStakeholders] = useState<StakeholderRole[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [tab, setTab] = useState<Tab>('questions');
  const [editor, setEditor] = useState<Editor | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    Promise.all([api<ChecklistSection[]>(path + 'sections/'), api<StakeholderRole[]>(path + 'stakeholders/'), api<Question[]>(path + 'questions/')])
      .then(([nextSections, nextRoles, nextQuestions]) => {if (active) {setSections(nextSections); setStakeholders(nextRoles); setQuestions(nextQuestions);}})
      .catch(err => {if (active) setError(checklistError(err));})
      .finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [path, retry]);
  function open(next: Editor) {setEditor(next); setError(''); setSuccess('');}
  async function saveQuestion(data: QuestionInput) {
    if (editor?.kind !== 'question') return;
    const initial = editor.initial;
    const result = await api<Question>(path + 'questions/' + (initial ? `${initial.id}/` : ''), initial ? 'PATCH' : 'POST', data);
    setQuestions(current => (initial ? current.map(item => item.id === result.id ? result : item) : [...current, result]).sort((a,b) => a.order_index - b.order_index));
    setEditor(null); setSuccess(initial ? 'Questão atualizada.' : 'Questão cadastrada.');
  }
  async function saveStructure(data: {name: string; description?: string}) {
    if (!editor || editor.kind === 'question') return;
    const {kind, initial} = editor;
    const endpoint = kind === 'section' ? 'sections/' : 'stakeholders/';
    const result = await api<ChecklistSection & StakeholderRole>(path + endpoint + (initial ? `${initial.id}/` : ''), initial ? 'PATCH' : 'POST', data);
    if (kind === 'section') {
      setSections(current => initial ? current.map(item => item.id === result.id ? result : item) : [...current, result]);
      setQuestions(current => current.map(item => item.section?.id === result.id ? {...item, section: result} : item));
    } else {
      setStakeholders(current => (initial ? current.map(item => item.id === result.id ? result : item) : [...current, result]).sort((a,b) => a.name.localeCompare(b.name, 'pt-BR') || a.id - b.id));
      setQuestions(current => current.map(item => ({...item, stakeholders: item.stakeholders.map(role => role.id === result.id ? result : role)})));
    }
    setEditor(null); setSuccess(kind === 'section' ? 'Seção salva.' : 'Stakeholder salvo.');
  }
  async function reorder(kind: 'sections' | 'questions', ids: number[]) {
    setBusy(true); setError(''); setSuccess('');
    try {
      if (kind === 'sections') setSections(await api<ChecklistSection[]>(path + 'sections/reorder/', 'POST', {ids}));
      else setQuestions(await api<Question[]>(path + 'questions/reorder/', 'POST', {ids}));
      setSuccess('Ordem atualizada.');
    } catch (err) {setError(checklistError(err));} finally {setBusy(false);}
  }
  function moveQuestion(group: Question[], index: number, direction: -1 | 1) {
    const ids = questions.map(item => item.id);
    const first = ids.indexOf(group[index].id);
    const second = ids.indexOf(group[index + direction].id);
    [ids[first], ids[second]] = [ids[second], ids[first]];
    void reorder('questions', ids);
  }
  function groupContent(section: ChecklistSection | null) {
    const group = questions.filter(item => (item.section?.id ?? null) === (section?.id ?? null));
    if (!section && group.length === 0 && sections.length > 0) return null;
    return <section className="question-group" key={section?.id ?? 'unsectioned'} aria-label={section?.name ?? 'Questões sem seção'}>
      <h3>{section?.name ?? 'Sem seção'}</h3>
      {group.length ? <ol className="question-list">{group.map((question, index) => <li className="card question-card" key={question.id}>
        <h4>{index + 1}. {question.statement}</h4>
        <p className="muted">{question.response_type === 'TEXT' ? 'Texto' : 'Seleção única'} · {commentLabels[question.comment_mode]}</p>
        <p className="muted">{question.stakeholders.length ? `Stakeholders: ${question.stakeholders.map(role => role.name).join(', ')}` : 'Comum a todos os participantes'}</p>
        {question.options.length > 0 && <details><summary>Opções de resposta ({question.options.length})</summary><ol className="option-preview">{question.options.map(option => <li key={option.id}>{option.label}</li>)}</ol></details>}
        {canEdit && <div className="actions"><button className="secondary" disabled={!!editor || busy} aria-label={`Editar questão ${question.statement}`} onClick={() => open({kind:'question', initial: question})}>Editar questão</button>
          <MoveControls label={`questão ${question.statement}`} index={index} count={group.length} disabled={busy || !!editor} onMove={direction => moveQuestion(group, index, direction)} /></div>}
      </li>)}</ol> : <EmptyState title="Nenhuma questão nesta seção" />}
    </section>;
  }
  const title = tabs.find(item => item.id === tab)!.label;
  return <div className="page-stack checklist-structure">
    <div className="tabs" role="tablist" aria-label="Áreas da checklist" onKeyDown={event => {
      if (['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) {
        event.preventDefault();
        const index = tabs.findIndex(item => item.id === tab);
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (index + (event.key === 'ArrowRight' ? 1 : 2)) % 3;
        setTab(tabs[next].id); document.getElementById(`chk-tab-${tabs[next].id}`)?.focus();
      }
    }}>{tabs.map(item => <button key={item.id} id={`chk-tab-${item.id}`} role="tab" aria-controls={`chk-panel-${item.id}`} aria-selected={tab === item.id} tabIndex={tab === item.id ? 0 : -1} onClick={() => {setTab(item.id); setSuccess('');}}>{item.label}</button>)}</div>
    {success && <Notice message={success} />}{error && <Notice message={error} error />}
    {loading ? <p role="status">Carregando estrutura da versão…</p> : error && !questions.length && !sections.length && !stakeholders.length ? <button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button> : <>
      <div className="section-heading"><h2>{title}</h2>{canEdit && <button disabled={busy || !!editor} onClick={() => open(tab === 'questions' ? {kind:'question', initial:null} : tab === 'sections' ? {kind:'section', initial:null} : {kind:'stakeholder', initial:null})}>
        {tab === 'questions' ? '+ Adicionar questão' : tab === 'sections' ? '+ Adicionar seção' : '+ Adicionar stakeholder'}</button>}</div>
      {tabs.map(item => <div key={item.id} id={`chk-panel-${item.id}`} role="tabpanel" aria-labelledby={`chk-tab-${item.id}`} hidden={tab !== item.id} tabIndex={0} className="page-stack">
        {item.id === 'questions' && (questions.length || sections.length ? <>{sections.map(groupContent)}{groupContent(null)}</> : <div className="card"><EmptyState title="Nenhuma questão cadastrada"><p>Você pode criar questões com ou sem seção e configurar suas próprias opções de resposta.</p></EmptyState></div>)}
        {item.id === 'sections' && (sections.length ? <ol className="structure-list">{sections.map((section, index) => <li className="card" key={section.id}><h3>{section.name}</h3>
          {canEdit && <div className="actions"><button className="secondary" disabled={busy || !!editor} aria-label={`Editar seção ${section.name}`} onClick={() => open({kind:'section', initial:section})}>Editar seção</button>
            <MoveControls label={`seção ${section.name}`} index={index} count={sections.length} disabled={busy || !!editor} onMove={direction => {void reorder('sections', moveItem(sections, index, direction).map(section => section.id));}} /></div>}</li>)}</ol>
          : <div className="card"><EmptyState title="Nenhuma seção cadastrada"><p>As seções são opcionais. Questões podem permanecer sem seção.</p></EmptyState></div>)}
        {item.id === 'stakeholders' && (stakeholders.length ? <ul className="structure-list">{stakeholders.map(role => <li className="card" key={role.id}><h3>{role.name}</h3><p className="muted preserve-lines">{role.description || 'Sem descrição.'}</p>
          {canEdit && <button className="secondary" disabled={busy || !!editor} aria-label={`Editar stakeholder ${role.name}`} onClick={() => open({kind:'stakeholder', initial:role})}>Editar stakeholder</button>}</li>)}</ul>
          : <div className="card"><EmptyState title="Nenhum stakeholder cadastrado"><p>Os papéis são definidos por você, nesta versão da checklist.</p></EmptyState></div>)}
      </div>)}
      {canEdit && editor?.kind === 'question' && <QuestionEditor initial={editor.initial} sections={sections} stakeholders={stakeholders} onSave={saveQuestion} onClose={() => setEditor(null)} />}
      {canEdit && editor && editor.kind !== 'question' && <StructureEditor kind={editor.kind} initial={editor.initial} onSave={saveStructure} onClose={() => setEditor(null)} />}
    </>}
  </div>;
}
