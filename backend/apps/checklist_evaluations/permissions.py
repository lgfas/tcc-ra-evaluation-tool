from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import ChecklistEvaluation


def accessible_evaluations(user):
    return ChecklistEvaluation.objects.filter(Q(created_by_user=user) | Q(participants__user=user)).distinct()


def require_creator(evaluation, user):
    if evaluation.created_by_user_id != user.pk:
        raise PermissionDenied('Somente o criador pode configurar ou iniciar esta avaliação.')


def require_draft(evaluation):
    if evaluation.status != ChecklistEvaluation.Status.DRAFT:
        raise ValidationError({'detail': 'A configuração só pode ser alterada enquanto a avaliação está em DRAFT.'})
