from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import ChecklistEvaluation


def accessible_evaluations(user):
    return ChecklistEvaluation.objects.filter(Q(created_by_user=user) | Q(participants__user=user)).distinct()


def require_creator(evaluation, user):
    if evaluation.created_by_user_id != user.pk:
        raise PermissionDenied('Esta operação é permitida somente ao criador da avaliação.')


def require_draft(evaluation):
    if evaluation.status != ChecklistEvaluation.Status.DRAFT:
        raise ValidationError({'detail': 'A configuração só pode ser alterada enquanto a avaliação está em DRAFT.'})


def participant_for(user, evaluation_id):
    from django.shortcuts import get_object_or_404
    from .models import EvaluationParticipant

    # Creator status alone never grants access to the response workspace.
    return get_object_or_404(EvaluationParticipant.objects.select_related(
        'user', 'checklist_evaluation__ra_version__reference_architecture',
        'checklist_evaluation__checklist_version__checklist'),
        checklist_evaluation_id=evaluation_id, user=user)


def require_in_progress(evaluation):
    if evaluation.status != ChecklistEvaluation.Status.IN_PROGRESS:
        message = ('A avaliação ainda não foi iniciada.' if evaluation.status == ChecklistEvaluation.Status.DRAFT
                   else 'A avaliação está concluída e não aceita alterações nas respostas.')
        raise ValidationError({'detail': message})


def available_questions(participant, *, candidates=None):
    from apps.checklists.models import Question

    evaluation = participant.checklist_evaluation
    if candidates is not None:
        # Bulk reports pass prefetched questions and roles: same union, without N+1 queries.
        roles = {role.pk for role in participant.stakeholder_roles.all()
                 if role.checklist_version_id == evaluation.checklist_version_id}
        return [question for question in candidates
                if question.checklist_version_id == evaluation.checklist_version_id
                and (not question.stakeholders.all() or
                     any(role.pk in roles for role in question.stakeholders.all()))]
    roles = participant.stakeholder_roles.filter(checklist_version_id=evaluation.checklist_version_id)
    return Question.objects.filter(checklist_version_id=evaluation.checklist_version_id).filter(
        Q(stakeholders__isnull=True) | Q(stakeholders__in=roles)).distinct().order_by('order_index', 'id')
