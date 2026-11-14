import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api } from '../../services/api';
import { evaluationBase as base, evaluationError, statusLabels, type Evaluation, type EvaluationProgress, type EvaluationResults } from '../../services/evaluations';
import PageHeader from '../PageHeader';
import StatCard from '../StatCard';
import Notice from '../Notice';
import EmptyState from '../EmptyState';
import EditorPanel from '../EditorPanel';

const percent = (value: number | null) => value === null ? 'Não aplicável' : `${value.toLocaleString('pt-BR')}%`;
export default function EvaluationMonitoring({evaluation, onStatus}: {evaluation: Evaluation; onStatus: (status: Evaluation['status']) => void}) {
  const [progress, setProgress] = useState<EvaluationProgress | null>(null);
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [tab, setTab] = useState<'progress' | 'results'>(evaluation.status === 'COMPLETED' ? 'results' : 'progress');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [retry, setRetry] = useState(0);
  const [confirming, setConfirming] = useState(false);
  const [confirmIncomplete, setConfirmIncomplete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [panelError, setPanelError] = useState('');
  const submitting = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const path = `${base}${evaluation.id}/`;
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    async function load() {
      const next = await api<EvaluationProgress>(path + 'progress/');
      const consolidated = next.status === 'COMPLETED' ? await api<EvaluationResults>(path + 'results/') : null;
      if (!active) return;
      setProgress(next); setResults(consolidated);
      if (next.status !== evaluation.status) onStatus(next.status);
      if (next.status === 'COMPLETED') setTab('results');
    }
    void load().catch(err => {if (active) setError(evaluationError(err));}).finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [path, retry, evaluation.status]); // onStatus only updates the parent status; it does not trigger a request.
  async function openCompletion() {
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError(''); setSuccess('');
    try {
      const current = await api<EvaluationProgress>(path + 'progress/');
      setProgress(current);
      if (current.status !== 'IN_PROGRESS') {onStatus(current.status); return;}
      setConfirmIncomplete(false); setPanelError(''); setConfirming(true);
    } catch (err) {setError(evaluationError(err));} finally {submitting.current = false; setBusy(false);}
  }
  async function complete(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setPanelError('');
    try {
      const result = await api<{id: number; status: Evaluation['status']}>(path + 'complete/', 'POST', {confirm_incomplete:confirmIncomplete});
      setConfirming(false); setTab('results'); setSuccess('Avaliação finalizada. As respostas foram preservadas e não podem mais ser alteradas.');
      onStatus(result.status);
      requestAnimationFrame(() => heading.current?.focus());
    } catch (err) {
      setPanelError(evaluationError(err));
      // Counts are advisory in the dialog; completion always recalculates them under the server lock.
      try {setProgress(await api<EvaluationProgress>(path + 'progress/'));} catch { /* Preserve the original failure. */ }
    } finally {submitting.current = false; setBusy(false);}
  }
  const totals = progress?.totals;
  return <section className="page-stack evaluation-page"><PageHeader title={`Avaliação da ${evaluation.ra_version.architecture_name}`} eyebrow={<a href="#/evaluations">Avaliação por checklist</a>}
    badge={<span className="badge badge-dark">{evaluation.status} · {statusLabels[evaluation.status]}</span>}
    actions={<div className="actions">{evaluation.is_participant && evaluation.status === 'IN_PROGRESS' && <a className="button-link secondary" href={`#/evaluations/${evaluation.id}/respond`}>Responder avaliação</a>}{evaluation.status === 'IN_PROGRESS' && <button disabled={busy || loading} onClick={() => void openCompletion()}>{busy ? 'Aguarde…' : 'Finalizar avaliação'}</button>}</div>} />
    <div className="response-context"><span>Checklist: {evaluation.checklist_version.checklist_name} · v{evaluation.checklist_version.version} · RA: v{evaluation.ra_version.version}</span><span>Criada em {new Date(evaluation.created_at).toLocaleString('pt-BR')}</span></div>
    <nav className="tabs" aria-label="Áreas da avaliação"><button aria-pressed={tab === 'progress'} className={tab === 'progress' ? 'is-active' : ''} onClick={() => setTab('progress')}>Acompanhamento</button><button aria-pressed={tab === 'results'} className={tab === 'results' ? 'is-active' : ''} disabled={evaluation.status !== 'COMPLETED'} onClick={() => setTab('results')}>Resultados</button></nav>
    {success && <Notice message={success} />}{error && <Notice message={error} error />}
    <div className="section-heading"><h2 ref={heading} tabIndex={-1}>{tab === 'progress' ? 'Acompanhamento da avaliação' : 'Resultados consolidados'}</h2><button className="secondary" disabled={loading || busy} onClick={() => setRetry(value => value + 1)}>Atualizar dados</button></div>
    {loading ? <p role="status">Carregando dados da avaliação…</p> : error ? <p>Tente novamente usando Atualizar dados.</p> : progress && totals && <>
      <div className="stats-grid"><StatCard label="Participantes" value={totals.participants} /><StatCard label="Respostas registradas" value={totals.answered} hint={`${totals.pending} pendente(s)`} /><StatCard label="Respostas esperadas" value={totals.expected} /><StatCard label="Progresso geral" value={percent(totals.percentage)} hint={totals.percentage === null ? 'Nenhuma questão atribuída' : 'Das respostas esperadas'} /></div>
      {tab === 'progress' ? <div className="monitoring-columns"><section className="page-stack"><h3>Progresso dos participantes</h3><p className="muted">Cada total considera somente questões comuns ou associadas aos papéis do participante. O progresso usa respostas salvas.</p>
        {progress.participants.map(participant => <article key={participant.id} className="card page-stack participant-progress"><div className="section-heading"><div><h4>{participant.user.name}</h4><p className="muted">{participant.stakeholder_roles.map(role => role.name).join(', ') || 'Somente questões comuns'}</p></div><strong>{percent(participant.percentage)}</strong></div>
          {participant.total ? <><span>{participant.answered} de {participant.total} respondidas · {participant.pending} pendente(s)</span><progress className="answer-progress" value={participant.answered} max={participant.total} aria-label={`Progresso de ${participant.user.name}`} />
            {!!participant.pending && <details><summary>Questões pendentes ({participant.pending})</summary><ul>{participant.pending_questions.map(question => <li key={question.id}>{question.statement}</li>)}</ul></details>}</> : <p>Nenhuma questão atribuída</p>}
        </article>)}
      </section><aside className="card monitoring-note page-stack"><h3>{evaluation.status === 'COMPLETED' ? 'Avaliação concluída' : 'Preenchimento em andamento'}</h3><p>{evaluation.status === 'COMPLETED' ? 'Não são aceitas novas respostas. Respostas ausentes permanecem identificadas como Não respondida.' : 'Os participantes podem revisar suas respostas até a finalização. Os resultados consolidados estarão disponíveis após o encerramento.'}</p><h4>Questões comuns</h4><p>Questões sem stakeholders são atribuídas a todos os participantes e contam uma vez para cada participante.</p><p className="muted">Nenhuma questão atribuída significa progresso não aplicável, sem pendências.</p></aside></div>
      : results && <section className="page-stack" aria-label="Questões e respostas"><p className="preservation-note">Resultados das respostas persistidas. Ausência de resposta não representa uma alternativa negativa. As distribuições consideram somente respostas válidas.</p>
        {results.questions.length ? results.questions.map((question, index) => <article className="card page-stack question-result" key={question.id}><div className="section-heading"><span className="badge">{question.section?.name || 'Sem seção'}</span><span className="muted">{question.response_type === 'TEXT' ? 'Resposta textual' : 'Seleção única'}</span></div><h3>{index + 1}. {question.statement}</h3>
          <p className="muted">{question.stakeholder_roles.map(role => role.name).join(', ') || 'Comum a todos os participantes'} · {question.answered} resposta(s) válida(s) · {question.pending} não respondida(s)</p>
          {question.response_type === 'SINGLE_CHOICE' && <section className="page-stack" aria-label="Distribuição das alternativas"><h4>Distribuição entre respostas válidas</h4>{!question.answered && <p>Nenhuma resposta registrada para esta questão.</p>}{question.distribution.map(option => <div className="distribution-option" key={option.id}><div className="section-heading"><span>{option.label}</span><strong>{option.count} · {percent(option.percentage)}</strong></div><progress className="answer-progress" max={100} value={option.percentage ?? 0} aria-label={`Distribuição: ${option.label}`} /></div>)}</section>}
          <section className="page-stack"><h4>Respostas individuais</h4>{question.responses.length ? question.responses.map(row => <div className="result-response" key={row.participant_id}><strong>{results.participants.find(participant => participant.id === row.participant_id)?.user.name}</strong>{row.answer ? <><p className="preserve-lines">{question.response_type === 'TEXT' ? row.answer.text_value : question.distribution.find(option => option.id === row.answer?.response_option_id)?.label}</p>{row.answer.comment && <div><span className="muted">Comentário</span><p className="preserve-lines">{row.answer.comment}</p></div>}</> : <p className="muted">Não respondida</p>}</div>) : <EmptyState title="Nenhum participante recebeu esta questão" />}</section>
        </article>) : <EmptyState title="Nenhuma questão nesta avaliação" />}
      </section>}
    </>}
    {confirming && totals && <EditorPanel title="Finalizar avaliação" busy={busy} onClose={() => {setConfirming(false); setPanelError('');}}>
      {panelError && <Notice message={panelError} error />}<form onSubmit={complete}><p>O encerramento impedirá novas respostas e alterações. Esta ação não poderá ser desfeita.</p>
        {totals.pending > 0 ? <><Notice message={`Existem ${totals.pending} resposta(s) pendente(s) de ${totals.participants_with_pending} participante(s). Os resultados mostrarão essas ausências como “Não respondida”.`} error /><label className="checkbox-row"><input type="checkbox" checked={confirmIncomplete} disabled={busy} onChange={event => setConfirmIncomplete(event.target.checked)} />Confirmo a finalização com respostas pendentes.</label></> : <p>Não há respostas pendentes. Confirma a finalização da avaliação?</p>}
        <div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={() => setConfirming(false)}>Cancelar</button><button disabled={busy || (totals.pending > 0 && !confirmIncomplete)}>{busy ? 'Finalizando…' : 'Confirmar finalização'}</button></div>
      </form></EditorPanel>}
  </section>;
}
