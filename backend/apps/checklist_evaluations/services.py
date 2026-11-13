from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from apps.reference_architectures.models import RAVersion
from apps.reference_architectures.permissions import accessible_architectures
from apps.checklists.models import ChecklistVersion, Question, StakeholderRole
from apps.checklists.permissions import accessible_checklists
from .models import ChecklistEvaluation, EvaluationParticipant, ParticipantRole
from .permissions import require_creator, require_draft


def locked_evaluation(*, evaluation, user):
    evaluation = ChecklistEvaluation.objects.select_for_update(of=('self',)).get(pk=evaluation.pk)
    require_creator(evaluation, user)
    require_draft(evaluation)
    return evaluation


def lock_versions(*, ra_version_id, checklist_version_id, user):
    # Canonical order for all evaluation mutations: evaluation -> RA version -> checklist version.
    # of=('self',) avoids implicitly locking joined parent rows in a different order.
    ra = get_object_or_404(RAVersion.objects.select_for_update(of=('self',)), pk=ra_version_id)
    checklist = get_object_or_404(ChecklistVersion.objects.select_for_update(of=('self',)), pk=checklist_version_id)
    validate_access(user=user, ra=ra, checklist=checklist)
    return ra, checklist


def validate_access(*, user, ra, checklist):
    if not accessible_architectures(user).filter(pk=ra.reference_architecture_id).exists():
        raise ValidationError({'ra_version_id': ['A versão da RA não existe ou não está acessível.']})
    if not accessible_checklists(user).filter(pk=checklist.checklist_id).exists():
        raise ValidationError({'checklist_version_id': ['A versão da checklist não existe ou não está acessível.']})


@transaction.atomic
def create_evaluation(*, user, ra_version_id, checklist_version_id):
    # Filter before locking so arbitrary IDs do not reveal private artifacts.
    ra = get_object_or_404(RAVersion, pk=ra_version_id, reference_architecture__in=accessible_architectures(user))
    checklist = get_object_or_404(ChecklistVersion, pk=checklist_version_id, checklist__in=accessible_checklists(user))
    lock_versions(user=user, ra_version_id=ra.pk, checklist_version_id=checklist.pk)
    return ChecklistEvaluation.objects.create(created_by_user=user, ra_version=ra, checklist_version=checklist)


@transaction.atomic
def update_versions(*, user, evaluation, data):
    evaluation = locked_evaluation(evaluation=evaluation, user=user)
    ra_id = data.get('ra_version_id', evaluation.ra_version_id)
    checklist_id = data.get('checklist_version_id', evaluation.checklist_version_id)
    # Resolve only accessible selections, including when they were public and became private.
    get_object_or_404(RAVersion, pk=ra_id, reference_architecture__in=accessible_architectures(user))
    get_object_or_404(ChecklistVersion, pk=checklist_id, checklist__in=accessible_checklists(user))
    ra, checklist = lock_versions(user=user, ra_version_id=ra_id, checklist_version_id=checklist_id)
    if checklist.pk != evaluation.checklist_version_id:
        ParticipantRole.objects.filter(evaluation_participant__checklist_evaluation=evaluation).delete()
    evaluation.ra_version = ra
    evaluation.checklist_version = checklist
    evaluation.save(update_fields=['ra_version', 'checklist_version'])
    return evaluation


def validated_roles(*, evaluation, ids):
    if len(ids) != len(set(ids)):
        raise ValidationError({'stakeholder_role_ids': ['Não repita papéis.']})
    roles = list(StakeholderRole.objects.filter(checklist_version_id=evaluation.checklist_version_id, pk__in=ids))
    if len(roles) != len(ids):
        raise ValidationError({'stakeholder_role_ids': ['Todos os papéis devem pertencer à versão de checklist selecionada.']})
    return roles


@transaction.atomic
def save_participant(*, user, evaluation, stakeholder_role_ids, email=None, participant=None):
    evaluation = locked_evaluation(evaluation=evaluation, user=user)
    # Synchronize with structural writes and version changes before resolving roles.
    lock_versions(user=user, ra_version_id=evaluation.ra_version_id, checklist_version_id=evaluation.checklist_version_id)
    roles = validated_roles(evaluation=evaluation, ids=stakeholder_role_ids)
    if participant is None:
        account = get_user_model().objects.filter(email__iexact=email).first()
        if account is None:
            raise ValidationError({'email': ['Nenhum usuário cadastrado com este e-mail.']})
        if evaluation.participants.filter(user=account).exists():
            raise ValidationError({'email': ['Este usuário já participa da avaliação.']})
        participant = EvaluationParticipant.objects.create(checklist_evaluation=evaluation, user=account)
    else:
        participant = get_object_or_404(evaluation.participants, pk=participant.pk)
    participant.role_links.all().delete()
    ParticipantRole.objects.bulk_create([
        ParticipantRole(evaluation_participant=participant, stakeholder_role=role) for role in roles
    ])
    return participant


@transaction.atomic
def remove_participant(*, user, evaluation, participant):
    evaluation = locked_evaluation(evaluation=evaluation, user=user)
    get_object_or_404(evaluation.participants, pk=participant.pk).delete()


def validate_questions(version):
    questions = list(version.questions.select_related('section').prefetch_related('options', 'stakeholders'))
    if not questions:
        raise ValidationError({'detail': 'Cadastre ao menos uma questão válida na versão da checklist antes de iniciar.'})
    for question in questions:
        options = list(question.options.all())
        invalid = (
            not question.statement.strip()
            or question.response_type not in Question.ResponseType.values
            or question.comment_mode not in Question.CommentMode.values
            or (question.section_id is not None and question.section.checklist_version_id != version.pk)
            or any(role.checklist_version_id != version.pk for role in question.stakeholders.all())
            or (question.response_type == Question.ResponseType.SINGLE_CHOICE and not options)
            or (question.response_type == Question.ResponseType.TEXT and bool(options))
            or any(not option.label.strip() for option in options)
        )
        if invalid:
            raise ValidationError({'detail': 'Revise as questões da checklist: há uma configuração inválida nesta versão.'})


@transaction.atomic
def start_evaluation(*, user, evaluation):
    evaluation = locked_evaluation(evaluation=evaluation, user=user)
    ra, checklist = lock_versions(user=user, ra_version_id=evaluation.ra_version_id, checklist_version_id=evaluation.checklist_version_id)
    if not evaluation.participants.exists():
        raise ValidationError({'detail': 'Adicione ao menos um participante antes de iniciar.'})
    if ParticipantRole.objects.filter(evaluation_participant__checklist_evaluation=evaluation).exclude(
            stakeholder_role__checklist_version=checklist).exists():
        raise ValidationError({'detail': 'Há papéis de outra versão atribuídos aos participantes.'})
    validate_questions(checklist)
    evaluation.status = ChecklistEvaluation.Status.IN_PROGRESS
    evaluation.save(update_fields=['status'])
    return evaluation


@transaction.atomic
def save_answer(*, user, evaluation_id, question_id, data):
    from django.core.exceptions import ValidationError as ModelValidationError
    from apps.checklists.models import ResponseOption
    from .models import Answer
    from .permissions import participant_for, require_in_progress, available_questions

    # Check participation before locking; re-resolve it after any concurrent configuration commits.
    participant_for(user, evaluation_id)
    evaluation = ChecklistEvaluation.objects.select_for_update(of=('self',)).get(pk=evaluation_id)
    participant = participant_for(user, evaluation_id)
    require_in_progress(evaluation)
    question = get_object_or_404(available_questions(participant), pk=question_id)
    option = None
    if data.get('response_option_id') is not None:
        option = ResponseOption.objects.filter(pk=data['response_option_id'], question=question).first()
        if option is None:
            raise ValidationError({'response_option_id': ['Selecione uma opção válida desta questão.']})
    answer = Answer.objects.filter(evaluation_participant=participant, question=question).first()
    if answer is None:
        answer = Answer(evaluation_participant=participant, question=question)
    answer.response_option = option
    answer.text_value = data.get('text_value', '')
    answer.comment = data.get('comment', '')
    try:
        answer.full_clean()
    except ModelValidationError as exc:
        raise ValidationError(exc.message_dict) from exc
    answer.save()
    return answer
