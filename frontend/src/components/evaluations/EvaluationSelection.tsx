import { useEffect, useId, useRef, useState } from 'react';
import { api } from '../../services/api';
import { evaluationBase, evaluationError, type EvaluationChoices, type VersionSelection } from '../../services/evaluations';
import Notice from '../Notice';

// Shared by initial creation and DRAFT revision. Contains no persistence of its own.
export default function EvaluationSelection({ initial, onChange, onReady, disabled = false }: {
  initial: VersionSelection; onChange: (value: VersionSelection) => void; onReady: (ready: boolean) => void; disabled?: boolean;
}) {
  const first = useRef(initial);
  const id = useId();
  const [choices, setChoices] = useState<EvaluationChoices>({architectures:[], checklists:[]});
  const [architectureId, setArchitectureId] = useState('');
  const [checklistId, setChecklistId] = useState('');
  const [value, setValue] = useState(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); onReady(false);
    api<EvaluationChoices>(evaluationBase + 'choices/').then(data => {
      if (!active) return;
      setChoices(data);
      const ra = data.architectures.find(item => item.versions.some(version => version.id === first.current.ra_version_id));
      const checklist = data.checklists.find(item => item.versions.some(version => version.id === first.current.checklist_version_id));
      setArchitectureId(ra ? String(ra.id) : ''); setChecklistId(checklist ? String(checklist.id) : '');
      const next = {ra_version_id: ra ? first.current.ra_version_id : 0, checklist_version_id: checklist ? first.current.checklist_version_id : 0};
      setValue(next); onChange(next); onReady(true);
    }).catch(err => {if (active) setError(evaluationError(err));}).finally(() => {if (active) setLoading(false);});
    return () => {active = false;};
  }, [onChange, onReady, retry]);
  function change(next: VersionSelection) {setValue(next); onChange(next);}
  const ra = choices.architectures.find(item => String(item.id) === architectureId);
  const checklist = choices.checklists.find(item => String(item.id) === checklistId);
  if (loading) return <p role="status">Carregando artefatos acessíveis…</p>;
  if (error) return <div><Notice message={error} error /><button type="button" onClick={() => setRetry(current => current + 1)}>Tentar novamente</button></div>;
  return <fieldset className="evaluation-selection" disabled={disabled}>
    {(!choices.architectures.length || !choices.checklists.length) && <p className="muted">Para criar uma avaliação, é necessário ter acesso a uma RA e a uma checklist com versões cadastradas.</p>}
    <label><span id={`${id}-ra`}>Arquitetura de Referência</span><select aria-labelledby={`${id}-ra`} required value={architectureId} onChange={event => {
      const selected = choices.architectures.find(item => String(item.id) === event.target.value);
      setArchitectureId(event.target.value); change({...value, ra_version_id:selected?.versions[0]?.id ?? 0});
    }}><option value="">Selecione uma arquitetura</option>{choices.architectures.map(item => <option key={item.id} value={item.id}>{item.name} · {item.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</option>)}</select></label>
    <label><span id={`${id}-ra-version`}>Versão da RA</span><select aria-labelledby={`${id}-ra-version`} required disabled={!ra} value={value.ra_version_id || ''} onChange={event => change({...value, ra_version_id:Number(event.target.value)})}>
      <option value="">Selecione uma versão</option>{ra?.versions.map(version => <option key={version.id} value={version.id}>{version.version}</option>)}</select></label>
    <label><span id={`${id}-checklist`}>Checklist</span><select aria-labelledby={`${id}-checklist`} required value={checklistId} onChange={event => {
      const selected = choices.checklists.find(item => String(item.id) === event.target.value);
      setChecklistId(event.target.value); change({...value, checklist_version_id:selected?.versions[0]?.id ?? 0});
    }}><option value="">Selecione uma checklist</option>{choices.checklists.map(item => <option key={item.id} value={item.id}>{item.name} · {item.visibility === 'PUBLIC' ? 'Pública' : 'Privada'}</option>)}</select></label>
    <label><span id={`${id}-checklist-version`}>Versão da checklist</span><select aria-labelledby={`${id}-checklist-version`} required disabled={!checklist} value={value.checklist_version_id || ''} onChange={event => change({...value, checklist_version_id:Number(event.target.value)})}>
      <option value="">Selecione uma versão</option>{checklist?.versions.map(version => <option key={version.id} value={version.id}>{version.version}</option>)}</select></label>
  </fieldset>;
}
