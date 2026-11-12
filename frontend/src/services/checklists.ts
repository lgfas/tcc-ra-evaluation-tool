export interface ChecklistVersion { id: number; version: string; created_at: string }
export interface ChecklistSummary {
  id: number; name: string; origin: string; visibility: 'PRIVATE' | 'PUBLIC';
  owner_user: number; can_edit: boolean; version_count: number;
}
export interface Checklist extends ChecklistSummary { versions: ChecklistVersion[] }
export interface ChecklistSection { id: number; name: string; order_index: number }
export interface StakeholderRole { id: number; name: string; description: string }
export interface ResponseOption { id: number; label: string; order_index: number }
export interface Question {
  id: number; statement: string; response_type: 'SINGLE_CHOICE' | 'TEXT';
  comment_mode: 'NONE' | 'OPTIONAL' | 'REQUIRED'; order_index: number;
  section: ChecklistSection | null; stakeholders: StakeholderRole[]; options: ResponseOption[];
}
export interface QuestionInput {
  statement: string; response_type: Question['response_type']; comment_mode: Question['comment_mode'];
  section_id: number | null; stakeholder_ids: number[]; options: {label: string; order_index: number}[];
}
export const checklistBase = '/checklists/';
export const checklistError = (error: unknown) => error instanceof Error ? error.message : 'Não foi possível concluir a operação.';
export const commentLabels = { NONE: 'Sem comentário', OPTIONAL: 'Comentário opcional', REQUIRED: 'Comentário obrigatório ao responder' };
