export const evaluationBase = '/checklist-evaluations/';
export const evaluationError = (error: unknown) => error instanceof Error ? error.message : 'Não foi possível concluir a operação.';
export const statusLabels = {DRAFT:'Rascunho', IN_PROGRESS:'Em andamento', COMPLETED:'Concluída'};
export interface EvaluationRole {id: number; name: string}
export interface Participant {id: number; user: {id: number; name: string; email: string}; stakeholder_roles: EvaluationRole[]}
export interface EvaluationSummary {
  id: number; status: keyof typeof statusLabels; created_at: string; is_creator: boolean; is_participant: boolean; can_configure: boolean;
  ra_version: {id: number; version: string; architecture_id: number; architecture_name: string};
  checklist_version: {id: number; version: string; checklist_id: number; checklist_name: string};
}
export interface Evaluation extends EvaluationSummary {
  own_participation: Participant | null;
  participants?: Participant[]; available_stakeholders?: EvaluationRole[];
  question_count?: number | null; artifacts_accessible?: boolean;
}
export interface VersionSelection {ra_version_id: number; checklist_version_id: number}
export interface ArtifactChoice {id: number; name: string; visibility: 'PUBLIC' | 'PRIVATE'; versions: {id: number; version: string}[]}
export interface EvaluationChoices {architectures: ArtifactChoice[]; checklists: ArtifactChoice[]}

export interface OwnAnswer {id: number; response_option_id: number | null; text_value: string; comment: string}
export interface AnswerValue {response_option_id: number | null; text_value: string; comment: string}
export interface MyQuestion {
  id: number; statement: string; response_type: 'SINGLE_CHOICE' | 'TEXT'; comment_mode: 'NONE' | 'OPTIONAL' | 'REQUIRED';
  order_index: number; section: {id: number; name: string; order_index: number} | null;
  options: {id: number; label: string; order_index: number}[]; answer: OwnAnswer | null;
}
export interface MyQuestions {
  evaluation: {id: number; status: keyof typeof statusLabels; ra_version: {version: string; architecture_name: string}; checklist_version: {version: string; checklist_name: string}};
  participant: {name: string; stakeholder_roles: EvaluationRole[]}; questions: MyQuestion[]; progress: {answered: number; total: number};
}
// One mounted response workspace can guard the existing hash navigation without a router dependency.
let navigationGuard: (() => boolean) | null = null;
export function registerAnswerNavigationGuard(guard: () => boolean) {
  navigationGuard = guard;
  return () => {if (navigationGuard === guard) navigationGuard = null;};
}
export function allowAnswerNavigation() {return navigationGuard?.() ?? true;}

export interface EvaluationTotals {
  participants: number; expected: number; answered: number; pending: number;
  percentage: number | null; participants_with_pending: number;
}
export interface ParticipantProgress {
  id: number; user: {id: number; name: string}; stakeholder_roles: EvaluationRole[];
  total: number; answered: number; pending: number; percentage: number | null;
  pending_questions: {id: number; statement: string}[];
}
export interface EvaluationProgress {
  id: number; status: EvaluationSummary['status']; totals: EvaluationTotals; participants: ParticipantProgress[];
}
export interface QuestionResult {
  id: number; statement: string; response_type: MyQuestion['response_type']; comment_mode: MyQuestion['comment_mode'];
  order_index: number; section: {id: number; name: string} | null; stakeholder_roles: EvaluationRole[];
  expected: number; answered: number; pending: number;
  distribution: {id: number; label: string; count: number; percentage: number | null}[];
  responses: {participant_id: number; answer: OwnAnswer | null}[];
}
export interface EvaluationResults extends EvaluationProgress {
  ra_version: {id: number; version: string; architecture_name: string};
  checklist_version: {id: number; version: string; checklist_name: string};
  questions: QuestionResult[];
}
