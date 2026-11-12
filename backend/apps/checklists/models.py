from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Checklist(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = 'PRIVATE', 'Privada'
        PUBLIC = 'PUBLIC', 'Pública'

    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='checklists')
    derived_from_checklist_version = models.ForeignKey(
        'ChecklistVersion', null=True, blank=True, on_delete=models.PROTECT, related_name='derived_checklists')
    name = models.CharField(max_length=255)
    origin = models.TextField(blank=True)
    visibility = models.CharField(max_length=7, choices=Visibility.choices)

    class Meta:
        ordering = ['name', 'id']
        constraints = [models.CheckConstraint(
            condition=models.Q(visibility__in=['PRIVATE', 'PUBLIC']), name='checklist_valid_visibility')]


class ChecklistVersion(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.UniqueConstraint(fields=['checklist', 'version'], name='checklist_unique_version')]


class ChecklistSection(models.Model):
    checklist_version = models.ForeignKey(ChecklistVersion, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=255)
    order_index = models.PositiveIntegerField()

    class Meta:
        ordering = ['order_index', 'id']
        constraints = [models.UniqueConstraint(
            fields=['checklist_version', 'order_index'], name='checklist_section_unique_order',
            deferrable=models.Deferrable.DEFERRED)]


class StakeholderRole(models.Model):
    checklist_version = models.ForeignKey(ChecklistVersion, on_delete=models.CASCADE, related_name='stakeholders')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name', 'id']


class Question(models.Model):
    class ResponseType(models.TextChoices):
        SINGLE_CHOICE = 'SINGLE_CHOICE', 'Seleção única'
        TEXT = 'TEXT', 'Texto'

    class CommentMode(models.TextChoices):
        NONE = 'NONE', 'Sem comentário'
        OPTIONAL = 'OPTIONAL', 'Opcional'
        REQUIRED = 'REQUIRED', 'Obrigatório ao responder'

    checklist_version = models.ForeignKey(ChecklistVersion, on_delete=models.CASCADE, related_name='questions')
    section = models.ForeignKey(ChecklistSection, null=True, blank=True, on_delete=models.PROTECT, related_name='questions')
    statement = models.TextField()
    response_type = models.CharField(max_length=13, choices=ResponseType.choices)
    comment_mode = models.CharField(max_length=8, choices=CommentMode.choices)
    order_index = models.PositiveIntegerField()
    stakeholders = models.ManyToManyField(StakeholderRole, through='QuestionStakeholder', related_name='questions')

    class Meta:
        ordering = ['order_index', 'id']
        constraints = [
            models.UniqueConstraint(fields=['checklist_version', 'order_index'], name='checklist_question_unique_order',
                                    deferrable=models.Deferrable.DEFERRED),
            models.CheckConstraint(condition=models.Q(response_type__in=['SINGLE_CHOICE', 'TEXT']), name='question_valid_response_type'),
            models.CheckConstraint(condition=models.Q(comment_mode__in=['NONE', 'OPTIONAL', 'REQUIRED']), name='question_valid_comment_mode'),
        ]

    def clean(self):
        if self.section_id and self.section.checklist_version_id != self.checklist_version_id:
            raise ValidationError({'section': 'A seção deve pertencer à mesma versão da questão.'})


class ResponseOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=255)
    order_index = models.PositiveIntegerField()

    class Meta:
        ordering = ['order_index', 'id']
        constraints = [models.UniqueConstraint(fields=['question', 'order_index'], name='question_option_unique_order')]


class QuestionStakeholder(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='stakeholder_links')
    stakeholder_role = models.ForeignKey(StakeholderRole, on_delete=models.PROTECT, related_name='question_links')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['question', 'stakeholder_role'], name='question_stakeholder_unique')]

    def clean(self):
        if self.question_id and self.stakeholder_role_id:
            if self.question.checklist_version_id != self.stakeholder_role.checklist_version_id:
                raise ValidationError('Questão e stakeholder devem pertencer à mesma versão.')
