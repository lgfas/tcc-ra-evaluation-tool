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
