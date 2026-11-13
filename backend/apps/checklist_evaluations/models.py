from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ChecklistEvaluation(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Rascunho'
        IN_PROGRESS = 'IN_PROGRESS', 'Em andamento'
        COMPLETED = 'COMPLETED', 'Concluída'

    ra_version = models.ForeignKey('reference_architectures.RAVersion', on_delete=models.PROTECT, related_name='checklist_evaluations')
    checklist_version = models.ForeignKey('checklists.ChecklistVersion', on_delete=models.PROTECT, related_name='evaluations')
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_checklist_evaluations')
    status = models.CharField(max_length=11, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.CheckConstraint(
            condition=models.Q(status__in=['DRAFT', 'IN_PROGRESS', 'COMPLETED']), name='checklist_evaluation_valid_status')]


class EvaluationParticipant(models.Model):
    checklist_evaluation = models.ForeignKey(ChecklistEvaluation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='evaluation_participations')
    stakeholder_roles = models.ManyToManyField('checklists.StakeholderRole', through='ParticipantRole', related_name='evaluation_participants')

    class Meta:
        ordering = ['id']
        constraints = [models.UniqueConstraint(fields=['checklist_evaluation', 'user'], name='evaluation_unique_participant')]


class ParticipantRole(models.Model):
    evaluation_participant = models.ForeignKey(EvaluationParticipant, on_delete=models.CASCADE, related_name='role_links')
    stakeholder_role = models.ForeignKey('checklists.StakeholderRole', on_delete=models.PROTECT, related_name='participant_links')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['evaluation_participant', 'stakeholder_role'], name='evaluation_participant_unique_role')]

    def clean(self):
        if self.evaluation_participant_id and self.stakeholder_role_id:
            version_id = self.evaluation_participant.checklist_evaluation.checklist_version_id
            if self.stakeholder_role.checklist_version_id != version_id:
                raise ValidationError('O papel deve pertencer à versão de checklist da avaliação.')


class Answer(models.Model):
    evaluation_participant = models.ForeignKey(EvaluationParticipant, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('checklists.Question', on_delete=models.PROTECT, related_name='answers')
    response_option = models.ForeignKey('checklists.ResponseOption', null=True, blank=True,
                                        on_delete=models.PROTECT, related_name='answers')
    text_value = models.TextField(blank=True, default='')
    comment = models.TextField(blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evaluation_participant', 'question'], name='evaluation_unique_answer'),
            models.CheckConstraint(condition=(
                models.Q(response_option__isnull=False, text_value='') |
                models.Q(response_option__isnull=True, text_value__regex=r'\S')
            ), name='answer_single_value'),
        ]

    def clean(self):
        from apps.checklists.models import Question

        errors = {}
        question = self.question
        if question.checklist_version_id != self.evaluation_participant.checklist_evaluation.checklist_version_id:
            errors['question'] = 'A questão não pertence à checklist desta avaliação.'
        if question.response_type == Question.ResponseType.SINGLE_CHOICE:
            if not self.response_option_id or self.response_option.question_id != question.pk:
                errors['response_option_id'] = 'Selecione uma opção válida desta questão.'
            if self.text_value:
                errors['text_value'] = 'Uma questão de seleção não aceita resposta textual.'
        else:
            if not self.text_value.strip():
                errors['text_value'] = 'Preencha a resposta textual.'
            if self.response_option_id:
                errors['response_option_id'] = 'Uma questão textual não aceita opção de seleção.'
        if question.comment_mode == Question.CommentMode.NONE and self.comment:
            errors['comment'] = 'Esta questão não permite comentário.'
        if question.comment_mode == Question.CommentMode.REQUIRED and not self.comment.strip():
            errors['comment'] = 'Preencha o comentário obrigatório.'
        if errors:
            raise ValidationError(errors)
