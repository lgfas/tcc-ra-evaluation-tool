import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import { evaluationBase as base, evaluationError, statusLabels, type Evaluation, type EvaluationSummary, type Participant, type VersionSelection } from '../services/evaluations';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';
import EditorPanel from '../components/EditorPanel';
import EvaluationSelection from '../components/evaluations/EvaluationSelection';
import ParticipantEditor from '../components/evaluations/ParticipantEditor';
import VersionsEditor from '../components/evaluations/VersionsEditor';

export function EvaluationList() {
  const [items, setItems] = useState<EvaluationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<EvaluationSummary[]>(base).then(data => {if (active) setItems(data);})
      .catch(err => {if (active) setError(evaluationError(err));}).finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [retry]);
  function group(title: string, evaluations: EvaluationSummary[]) {
    return <section className="page-stack"><h2>{title}</h2>{evaluations.length ? <ul className="architecture-grid">{evaluations.map(item => <li className="card" key={item.id}>
      <span className="badge">{statusLabels[item.status]}</span><h3><a href={`#/evaluations/${item.id}`}>{item.ra_version.architecture_name} · v{item.ra_version.version}</a></h3>
      <p>{item.checklist_version.checklist_name} · v{item.checklist_version.version}</p><small>Criada em {new Date(item.created_at).toLocaleString('pt-BR')}</small><a href={`#/evaluations/${item.id}`}>Abrir avaliação →</a>{item.is_participant && item.status === 'IN_PROGRESS' && <a className="button-link" href={`#/evaluations/${item.id}/respond`}>Responder avaliação</a>}
    </li>)}</ul> : <div className="card"><EmptyState title="Nenhuma avaliação nesta lista" /></div>}</section>;
  }
  return <section className="page-stack"><PageHeader title="Minhas Avaliações" eyebrow="Avaliações por checklist" actions={<a className="button-link" href="#/evaluations/new">+ Nova avaliação</a>} />
    {loading ? <p role="status">Carregando avaliações…</p> : error ? <><Notice message={error} error /><button onClick={() => setRetry(current => current + 1)}>Tentar novamente</button></> : <>
      {group('Criadas por mim', items.filter(item => item.is_creator))}{group('Minhas participações', items.filter(item => item.is_participant))}
    </>}
  </section>;
}

export function EvaluationCreate({ initialRaVersionId }: {initialRaVersionId: number}) {
  const [selection, setSelection] = useState<VersionSelection>({ra_version_id:initialRaVersionId, checklist_version_id:0});
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submitting = useRef(false);
  async function create(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError('');
    try {
      const evaluation = await api<Evaluation>(base, 'POST', selection);
      window.location.hash = `/evaluations/${evaluation.id}`;
      // Keep the guard until this form unmounts: repeated clicks cannot create another draft.
    } catch (err) {setError(evaluationError(err)); submitting.current = false; setBusy(false);}
  }
  return <section className="page-stack form-page"><PageHeader title="Nova avaliação por checklist" eyebrow={<a href="#/evaluations">← Minhas Avaliações</a>} />
    <div className="card"><p>Selecione uma versão de RA e uma versão de checklist. A avaliação será criada como rascunho, sem participantes automáticos.</p>
      {error && <Notice message={error} error />}<form onSubmit={create}>
        <EvaluationSelection initial={{ra_version_id:initialRaVersionId, checklist_version_id:0}} onChange={setSelection} onReady={setReady} disabled={busy} />
        <div className="actions form-actions"><button disabled={busy || !ready || !selection.ra_version_id || !selection.checklist_version_id}>{busy ? 'Criando…' : 'Criar avaliação'}</button></div>
      </form></div>
  </section>;
}

type Panel = {kind:'participant'; initial:Participant | null} | {kind:'versions'} | {kind:'start'} | {kind:'remove'; participant:Participant};
export function EvaluationDetail({ id }: {id: number}) {
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [retry, setRetry] = useState(0);
  const [panel, setPanel] = useState<Panel | null>(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(2);
  const submitting = useRef(false);
  const participantsHeading = useRef<HTMLHeadingElement>(null);
  const summary = useRef<HTMLElement>(null);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<Evaluation>(`${base}${id}/`).then(data => {if (active) setEvaluation(data);})
      .catch(err => {if (active) setError(evaluationError(err));}).finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [id, retry]);
  function open(next: Panel) {setPanel(next); setError(''); setSuccess('');}
  async function saveParticipant(email: string, roleIds: number[]) {
    if (panel?.kind !== 'participant') return;
    const initial = panel.initial;
    const result = await api<Participant>(`${base}${id}/participants/${initial ? `${initial.id}/` : ''}`, initial ? 'PATCH' : 'POST',
      initial ? {stakeholder_role_ids:roleIds} : {email, stakeholder_role_ids:roleIds});
    setEvaluation(current => current ? {...current, participants: initial ? current.participants?.map(item => item.id === result.id ? result : item) : [...(current.participants ?? []), result]} : current);
    setPanel(null); setSuccess('Participante salvo.');
  }
  async function confirmAction(event: FormEvent) {
    event.preventDefault();
    if (submitting.current || !panel || (panel.kind !== 'start' && panel.kind !== 'remove')) return;
    submitting.current = true; setBusy(true); setError('');
    try {
      if (panel.kind === 'start') {
        const result = await api<{status: Evaluation['status']}>(`${base}${id}/start/`, 'POST', {});
        setEvaluation(current => current ? {...current, status:result.status, can_configure:false, available_stakeholders:[]} : current);
        setSuccess('Avaliação iniciada. As versões e a configuração estão preservadas.');
        requestAnimationFrame(() => summary.current?.focus());
      } else {
        const participantId = panel.participant.id;
        await api(`${base}${id}/participants/${participantId}/`, 'DELETE');
        setEvaluation(current => current ? {...current, participants:current.participants?.filter(item => item.id !== participantId)} : current);
        setSuccess('Participante removido.');
        requestAnimationFrame(() => participantsHeading.current?.focus());
      }
      setPanel(null);
    } catch (err) {setError(evaluationError(err));} finally {submitting.current = false; setBusy(false);}
  }
  if (loading) return <p role="status">Carregando avaliação…</p>;
  if (!evaluation) return <section className="page-stack"><PageHeader title="Avaliação indisponível" /><Notice message={error || 'Não foi possível carregar a avaliação.'} error /><a href="#/evaluations">Voltar à listagem</a><button onClick={() => setRetry(current => current + 1)}>Tentar novamente</button></section>;
  const canEdit = evaluation.can_configure;
  const participants = evaluation.participants ?? [];
  const rolesUsed = new Set(participants.flatMap(item => item.stakeholder_roles.map(role => role.id))).size;
  const raLabel = `${evaluation.ra_version.architecture_name} · v${evaluation.ra_version.version}`;
  const checklistLabel = `${evaluation.checklist_version.checklist_name} · v${evaluation.checklist_version.version}`;
  return <section className="page-stack evaluation-page"><PageHeader title={`Avaliação da ${evaluation.ra_version.architecture_name}`} eyebrow={<a href="#/evaluations">Avaliação por checklist</a>}
    badge={<span className="badge">{evaluation.status} · {statusLabels[evaluation.status]}</span>}
    actions={evaluation.is_participant && evaluation.status === 'IN_PROGRESS' ? <a className="button-link" href={`#/evaluations/${id}/respond`}>Responder avaliação</a> : canEdit ? <span className="muted">Rascunho salvo</span> : undefined} />
    <p className="muted">Criada em {new Date(evaluation.created_at).toLocaleString('pt-BR')}</p>
    {evaluation.is_creator && <ol className="evaluation-steps" aria-label="Etapas da configuração">
      <li><button className="secondary" disabled={!canEdit} aria-current={step === 1 ? 'step' : undefined} onClick={() => {setStep(1); open({kind:'versions'});}}><span>1</span> Artefatos</button></li>
      <li><button className="secondary" aria-current={step === 2 ? 'step' : undefined} onClick={() => {setStep(2); participantsHeading.current?.focus();}}><span>2</span> Participantes</button></li>
      <li><button className="secondary" aria-current={step === 3 ? 'step' : undefined} onClick={() => {setStep(3); summary.current?.focus();}}><span>3</span> Revisão</button></li>
    </ol>}
    {error && (!panel || panel.kind === 'participant' || panel.kind === 'versions') && <Notice message={error} error />}{success && <Notice message={success} />}
    {evaluation.status !== 'DRAFT' && <p className="preservation-note">Avaliação iniciada: versões, participantes e papéis não podem mais ser alterados.</p>}
    <div className={`evaluation-columns ${!evaluation.is_creator ? 'participant-context' : ''}`}><div className="page-stack">
      <section className="card page-stack"><div className="section-heading"><h2>Artefatos selecionados</h2>{canEdit && <button className="secondary" onClick={() => open({kind:'versions'})}>Alterar versões</button>}</div>
        <dl className="artifact-pair"><div><dt>Arquitetura de Referência</dt><dd>{raLabel}</dd></div><div><dt>Checklist</dt><dd>{checklistLabel}</dd></div></dl>
      </section>
      {evaluation.is_creator ? <>
        {evaluation.artifacts_accessible === false && <Notice message="O acesso a um dos artefatos foi alterado. Revise a seleção antes de configurar ou iniciar a avaliação." error />}
        <div className="section-heading"><div><h2 ref={participantsHeading} tabIndex={-1}>Participantes</h2><p className="muted">Associe zero ou mais papéis a cada participante.</p></div>{canEdit && <button onClick={() => open({kind:'participant', initial:null})}>+ Adicionar participante</button>}</div>
        {participants.length ? <ul className="evaluation-participants">{participants.map(item => <li className="card participant-row" key={item.id}>
          <span className="participant-avatar" aria-hidden="true">{item.user.name.charAt(0).toLocaleUpperCase('pt-BR')}</span><div className="participant-identity"><strong>{item.user.name}</strong><small>{item.user.email}</small></div>
          <div className="participant-roles">{item.stakeholder_roles.length ? item.stakeholder_roles.map(role => <span className="badge" key={role.id}>{role.name}</span>) : <span className="badge">Somente questões comuns</span>}</div>
          {canEdit && <div className="actions"><button className="secondary" aria-label={`Editar papéis de ${item.user.name}`} onClick={() => open({kind:'participant', initial:item})}>Editar papéis</button><button className="secondary" aria-label={`Remover participante ${item.user.name}`} onClick={() => open({kind:'remove', participant:item})}>Remover</button></div>}
        </li>)}</ul> : <div className="card"><EmptyState title="Nenhum participante cadastrado"><p>Adicione contas existentes pelo e-mail exato. O criador não é incluído automaticamente.</p></EmptyState></div>}
        <aside className="preservation-note"><h3>Como as questões são definidas</h3><p>Participantes com papéis receberão as questões associadas a qualquer um dos seus papéis e as questões comuns. Sem papéis, receberão apenas as questões comuns.</p></aside>
      </> : <section className="card page-stack"><h2>Minha participação</h2><p>{evaluation.own_participation?.stakeholder_roles.length ? evaluation.own_participation.stakeholder_roles.map(role => role.name).join(', ') : 'Somente questões comuns a todos os participantes.'}</p>
        <p className="muted">{evaluation.status === 'DRAFT' ? 'A avaliação está em preparação e ainda não pode ser preenchida.' : evaluation.status === 'IN_PROGRESS' ? 'Use Responder avaliação para preencher suas questões.' : 'Esta avaliação está concluída e não aceita alterações nas respostas.'}</p></section>}
    </div>
    {evaluation.is_creator && <aside className="card evaluation-summary page-stack" ref={summary} tabIndex={-1} aria-label="Resumo da configuração"><h2>Resumo da configuração</h2>
      <dl><div><dt>Status</dt><dd>{evaluation.status}</dd></div><div><dt>RA</dt><dd>{raLabel}</dd></div><div><dt>Checklist</dt><dd>{checklistLabel}</dd></div>
        <div><dt>Participantes</dt><dd>{participants.length} usuário(s)</dd></div><div><dt>Papéis utilizados</dt><dd>{rolesUsed} papel(éis)</dd></div>
        <div><dt>Questões na versão</dt><dd>{evaluation.question_count ?? 'Indisponível'}</dd></div></dl>
      {canEdit && <><p className="muted">Ao iniciar, o conteúdo destas versões e a configuração dos participantes ficarão preservados.</p>
        <button disabled={!participants.length || !evaluation.question_count || !evaluation.artifacts_accessible} onClick={() => open({kind:'start'})}>Iniciar avaliação</button>
        {(!participants.length || !evaluation.question_count) && <small>É necessário ao menos um participante e uma questão válida antes do início.</small>}</>}
    </aside>}</div>
    {canEdit && panel?.kind === 'participant' && <ParticipantEditor initial={panel.initial} roles={evaluation.available_stakeholders ?? []} onSave={saveParticipant} onClose={() => setPanel(null)} />}
    {canEdit && panel?.kind === 'versions' && <VersionsEditor evaluation={evaluation} onSaved={next => {setEvaluation(next); setPanel(null); setSuccess('Seleção de versões salva.');}} onClose={() => setPanel(null)} />}
    {canEdit && panel && (panel.kind === 'start' || panel.kind === 'remove') && <EditorPanel title={panel.kind === 'start' ? 'Iniciar avaliação' : 'Remover participante'} busy={busy} onClose={() => {setPanel(null); setError('');}}>
      {error && <Notice message={error} error />}<form onSubmit={confirmAction}>
        {panel.kind === 'start' ? <><p>Revise a seleção antes de confirmar:</p><p>{raLabel}</p><p>{checklistLabel}</p><p>{participants.length} participante(s). Após iniciar, versões, participantes e papéis não poderão ser alterados.</p></> : <p>Remover {panel.participant.user.name} ({panel.participant.user.email}) deste rascunho?</p>}
        <div className="actions form-actions"><button type="button" className="secondary" disabled={busy} onClick={() => setPanel(null)}>Cancelar</button><button disabled={busy}>{busy ? 'Aguarde…' : panel.kind === 'start' ? 'Confirmar início' : 'Confirmar remoção'}</button></div>
      </form></EditorPanel>}
  </section>;
}
