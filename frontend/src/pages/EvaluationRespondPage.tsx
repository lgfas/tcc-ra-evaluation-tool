import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import { evaluationBase as base, evaluationError, registerAnswerNavigationGuard, type AnswerValue, type MyQuestions, type OwnAnswer } from '../services/evaluations';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';

const emptyAnswer = (): AnswerValue => ({response_option_id:null, text_value:'', comment:''});
const valueOf = (answer: OwnAnswer | null): AnswerValue => answer ? {response_option_id:answer.response_option_id, text_value:answer.text_value, comment:answer.comment} : emptyAnswer();
export default function EvaluationRespondPage({id}: {id: number}) {
  const [data, setData] = useState<MyQuestions | null>(null);
  const [index, setIndex] = useState(0);
  const [value, setValue] = useState<AnswerValue>(emptyAnswer);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [retry, setRetry] = useState(0);
  const submitting = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const current = data?.questions[index];
  const dirty = !!current && JSON.stringify(value) !== JSON.stringify(valueOf(current.answer));
  const pending = useRef({dirty, busy});
  pending.current = {dirty, busy};
  useEffect(() => {
    const unregister = registerAnswerNavigationGuard(() => !pending.current.busy && (!pending.current.dirty || window.confirm('Há alterações não salvas. Deseja descartá-las e sair?')));
    const unload = (event: BeforeUnloadEvent) => {if (pending.current.dirty || pending.current.busy) {event.preventDefault(); event.returnValue = '';}};
    window.addEventListener('beforeunload', unload);
    return () => {unregister(); window.removeEventListener('beforeunload', unload);};
  }, []);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<MyQuestions>(`${base}${id}/my-questions/`).then(result => {
      if (active) {setData(result); setIndex(0); setValue(valueOf(result.questions[0]?.answer ?? null));}
    }).catch(err => {if (active) setError(evaluationError(err));}).finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [id, retry]);
  function navigate(next: number) {
    if (!data || submitting.current || next === index || next < 0 || next >= data.questions.length) return;
    if (dirty && !window.confirm('Há alterações não salvas. Deseja descartá-las e trocar de questão?')) return;
    setIndex(next); setValue(valueOf(data.questions[next].answer)); setError(''); setSuccess('');
    requestAnimationFrame(() => heading.current?.focus());
  }
  async function save(event: FormEvent, advance = false) {
    event.preventDefault();
    if (!current || !data || submitting.current) return;
    submitting.current = true; setBusy(true); setError(''); setSuccess('');
    try {
      const payload = current.response_type === 'SINGLE_CHOICE' ? {response_option_id:value.response_option_id, comment:value.comment} : {text_value:value.text_value, comment:value.comment};
      const answer = await api<OwnAnswer>(`${base}${id}/my-answers/${current.id}/`, 'PUT', payload);
      setData(previous => previous ? {...previous, questions:previous.questions.map(question => question.id === current.id ? {...question, answer} : question)} : previous);
      if (advance && index + 1 < data.questions.length) {
        setIndex(index + 1); setValue(valueOf(data.questions[index + 1].answer));
        requestAnimationFrame(() => heading.current?.focus());
      } else {setValue(valueOf(answer));}
      setSuccess('Resposta salva.');
    } catch (err) {setError(evaluationError(err));} finally {submitting.current = false; setBusy(false);}
  }
  if (loading) return <p role="status">Carregando questões…</p>;
  if (!data) return <section className="page-stack"><PageHeader title="Responder avaliação" /><Notice message={error || 'Avaliação indisponível.'} error /><a href={`#/evaluations/${id}`}>Voltar à avaliação</a><button onClick={() => setRetry(value => value + 1)}>Tentar novamente</button></section>;
  const answered = data.questions.filter(question => question.answer !== null).length;
  return <section className="page-stack response-page"><PageHeader title={data.evaluation.ra_version.architecture_name} eyebrow={<a href={`#/evaluations/${id}`}>Avaliação por checklist · #{id}</a>}
    badge={<span className="badge badge-dark">IN_PROGRESS</span>} actions={<span className="muted">Participante: {data.participant.name}</span>} />
    <div className="response-context"><span>RA: v{data.evaluation.ra_version.version} · Checklist: {data.evaluation.checklist_version.checklist_name} · v{data.evaluation.checklist_version.version}</span><span>Papéis: {data.participant.stakeholder_roles.map(role => role.name).join(', ') || 'Somente questões comuns'}</span><strong aria-live="polite">{answered} de {data.questions.length} questões respondidas</strong></div>
    <progress className="answer-progress" max={data.questions.length || 1} value={answered} aria-label="Progresso individual" />
    {!current ? <div className="card"><EmptyState title="Nenhuma questão disponível"><p>Não há questões comuns ou associadas aos seus papéis nesta avaliação.</p></EmptyState></div> : <div className="response-workspace">
      <nav className="question-navigator" aria-label="Questões disponíveis"><h2>Questões</h2><ol>{data.questions.map((question, position) => <li key={question.id}>
        {(position === 0 || question.section?.id !== data.questions[position - 1].section?.id) && <p className="muted">{question.section?.name || 'Sem seção'}</p>}
        <button className="secondary" aria-current={position === index ? 'step' : undefined} disabled={busy} onClick={() => navigate(position)}><span aria-hidden="true">{question.answer ? '✓' : position + 1}</span>Questão {position + 1}<span className="sr-only">{question.answer ? 'Respondida' : 'Não respondida'}</span></button>
      </li>)}</ol></nav>
      <div className="page-stack"><form onSubmit={save}>
        <div className="card page-stack current-question"><div className="section-heading"><span className="muted">Questão {index + 1} de {data.questions.length}</span><span className="badge">{current.section?.name || 'Sem seção'}</span></div>
          <h2 ref={heading} tabIndex={-1} className="question-statement">{current.statement}</h2><p className="muted">{current.response_type === 'TEXT' ? 'Resposta textual.' : 'Selecione uma opção de resposta.'} {current.comment_mode === 'REQUIRED' ? 'Comentário obrigatório.' : current.comment_mode === 'OPTIONAL' ? 'Comentário opcional.' : 'Esta questão não permite comentário.'}</p>
          <fieldset disabled={busy} className="answer-fields"><legend className="sr-only">Sua resposta</legend>
            {current.response_type === 'SINGLE_CHOICE' ? <div className="answer-options">{current.options.map(option => <label key={option.id} className={`answer-option ${value.response_option_id === option.id ? 'selected' : ''}`}><input type="radio" name={`question-${current.id}`} required checked={value.response_option_id === option.id} onChange={() => setValue({...value, response_option_id:option.id})} />{option.label}</label>)}</div> : <label>Resposta textual<textarea required rows={6} value={value.text_value} onChange={event => setValue({...value, text_value:event.target.value})} /></label>}
            {current.comment_mode !== 'NONE' && <label>Comentário ({current.comment_mode === 'REQUIRED' ? 'obrigatório' : 'opcional'})<textarea required={current.comment_mode === 'REQUIRED'} rows={4} value={value.comment} onChange={event => setValue({...value, comment:event.target.value})} placeholder="Adicione uma justificativa ou observação sobre sua resposta…" /></label>}
          </fieldset>
          {error && <Notice message={error} error />}{success && <Notice message={success} />}<small className="muted">{dirty ? 'Alterações ainda não salvas.' : current.answer ? 'Resposta persistida.' : 'Esta questão ainda não foi respondida.'}</small>
        </div>
        <div className="response-actions"><button type="button" className="secondary" disabled={busy || index === 0} onClick={() => navigate(index - 1)}>← Questão anterior</button><div className="actions"><button disabled={busy} className="secondary">{busy ? 'Salvando…' : 'Salvar resposta'}</button>{index + 1 < data.questions.length && <button disabled={busy} type="submit" onClick={event => {event.preventDefault(); const form = event.currentTarget.form; if (form?.reportValidity()) void save(event, true);}}>Salvar e próxima →</button>}<button type="button" className="secondary" disabled={busy || index + 1 >= data.questions.length} onClick={() => navigate(index + 1)}>Próxima questão →</button></div></div>
      </form><p className="muted">Questões sem stakeholder associado são disponibilizadas a todos os participantes. O progresso considera apenas respostas salvas.</p></div>
    </div>}
  </section>;
}
