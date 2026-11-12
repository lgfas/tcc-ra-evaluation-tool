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
