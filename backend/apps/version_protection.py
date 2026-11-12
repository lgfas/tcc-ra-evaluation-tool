"""Historical checks shared by domain services; callers must hold the version row lock."""
from django.apps import apps
from rest_framework.exceptions import ValidationError


def version_is_frozen(*, ra_version_id=None, checklist_version_id=None):
    evaluation = apps.get_model('checklist_evaluations', 'ChecklistEvaluation')
    field, value = ('ra_version_id', ra_version_id) if ra_version_id is not None else ('checklist_version_id', checklist_version_id)
    return evaluation.objects.filter(**{field: value}, status__in=['IN_PROGRESS', 'COMPLETED']).exists()


def require_editable_version(**version):
    if version_is_frozen(**version):
        raise ValidationError({'detail': 'Esta versão é utilizada por uma avaliação iniciada ou concluída. Crie uma nova versão para alterar seu conteúdo.'})
