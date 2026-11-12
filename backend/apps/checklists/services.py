from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from .models import Checklist, ChecklistVersion, ChecklistSection, StakeholderRole, Question, ResponseOption, QuestionStakeholder
from .permissions import require_owner


def writable_version(*, version, user):
    """All structural writes lock this row, serializing ordering and nested updates.

    Future evaluation usage checks must be added here before allowing any write.
    No evaluation entities exist yet; historical locking is not implemented.
    """
    version = ChecklistVersion.objects.select_for_update().select_related('checklist').get(pk=version.pk)
    require_owner(version.checklist, user)
    return version


@transaction.atomic
def create_checklist(*, user, initial_version, **metadata):
    checklist = Checklist.objects.create(owner_user=user, **metadata)
    ChecklistVersion.objects.create(checklist=checklist, **initial_version)
    return checklist


@transaction.atomic
def update_checklist(*, user, checklist, data):
    checklist = Checklist.objects.select_for_update().get(pk=checklist.pk)
    require_owner(checklist, user)
    for field in ('name', 'origin', 'visibility'):
        if field in data:
            setattr(checklist, field, data[field])
    checklist.save()
    return checklist


def create_version(*, user, checklist, **data):
    try:
        with transaction.atomic():
            checklist = Checklist.objects.select_for_update().get(pk=checklist.pk)
            require_owner(checklist, user)
            # Provisional CHK-01 choice: a new version starts empty, without copying.
            return ChecklistVersion.objects.create(checklist=checklist, **data)
    except IntegrityError as exc:
        if getattr(getattr(exc.__cause__, 'diag', None), 'constraint_name', None) == 'checklist_unique_version':
            raise ValidationError({'version': ['Já existe uma versão com este identificador nesta checklist.']}) from exc
        raise


def persist_order(items):
    for index, item in enumerate(items):
        item.order_index = index
    if items:
        type(items[0]).objects.bulk_update(items, ['order_index'])


def save_ordered(*, model, version, instance, data):
    items = list(model.objects.filter(checklist_version=version))
    if instance is None:
        index = data.pop('order_index', len(items))
        if index > len(items):
            raise ValidationError({'order_index': ['Posição fora da lista.']})
        instance = model.objects.create(checklist_version=version, order_index=len(items), **data)
    else:
        index = data.pop('order_index', instance.order_index)
        items = [item for item in items if item.pk != instance.pk]
        if index > len(items):
            raise ValidationError({'order_index': ['Posição fora da lista.']})
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
    items.insert(index, instance)
    persist_order(items)
    return instance


@transaction.atomic
def save_section(*, user, version, data, instance=None):
    version = writable_version(version=version, user=user)
    if instance is not None:
        instance = ChecklistSection.objects.get(pk=instance.pk, checklist_version=version)
    return save_ordered(model=ChecklistSection, version=version, instance=instance, data=dict(data))


@transaction.atomic
def save_stakeholder(*, user, version, data, instance=None):
    version = writable_version(version=version, user=user)
    if instance is None:
        return StakeholderRole.objects.create(checklist_version=version, **data)
    instance = StakeholderRole.objects.get(pk=instance.pk, checklist_version=version)
    for field in ('name', 'description'):
        if field in data:
            setattr(instance, field, data[field])
    instance.save()
    return instance


@transaction.atomic
def save_question(*, user, version, data, instance=None):
    version = writable_version(version=version, user=user)
    if instance is not None:
        instance = Question.objects.get(pk=instance.pk, checklist_version=version)
    data = dict(data)
    if 'section_id' in data and data['section_id'] is not None:
        if not version.sections.filter(pk=data['section_id']).exists():
            raise ValidationError({'section_id': ['A seção deve pertencer a esta versão.']})
    stakeholder_ids = data.pop('stakeholder_ids', None)
    if stakeholder_ids is not None:
        if len(set(stakeholder_ids)) != len(stakeholder_ids):
            raise ValidationError({'stakeholder_ids': ['Não repita stakeholders.']})
        if version.stakeholders.filter(pk__in=stakeholder_ids).count() != len(stakeholder_ids):
            raise ValidationError({'stakeholder_ids': ['Todos os stakeholders devem pertencer a esta versão.']})
    options = data.pop('options', None)
    response_type = data.get('response_type', instance.response_type if instance else None)
    if response_type == Question.ResponseType.TEXT:
        if options:
            raise ValidationError({'options': ['Questões textuais não possuem opções de seleção.']})
        options = []  # Switching to TEXT clears previously configured choices.
    else:
        if options is None:
            if instance is None or instance.response_type != Question.ResponseType.SINGLE_CHOICE:
                raise ValidationError({'options': ['Informe ao menos uma opção de resposta.']})
        elif not options:
            raise ValidationError({'options': ['Informe ao menos uma opção de resposta.']})
    if options is not None:
        if len({option['order_index'] for option in options}) != len(options):
            raise ValidationError({'options': ['As posições das opções não podem se repetir.']})
        options = sorted(options, key=lambda option: option['order_index'])
    question = save_ordered(model=Question, version=version, instance=instance, data=data)
    if options is not None:
        question.options.all().delete()
        ResponseOption.objects.bulk_create([
            ResponseOption(question=question, label=option['label'], order_index=index)
            for index, option in enumerate(options)
        ])
    if stakeholder_ids is not None:
        question.stakeholder_links.all().delete()
        QuestionStakeholder.objects.bulk_create([
            QuestionStakeholder(question=question, stakeholder_role_id=pk) for pk in stakeholder_ids
        ])
    return question


@transaction.atomic
def reorder(*, user, version, model, ids):
    version = writable_version(version=version, user=user)
    items = list(model.objects.filter(checklist_version=version))
    mapping = {item.pk: item for item in items}
    if len(ids) != len(set(ids)) or set(ids) != set(mapping):
        raise ValidationError({'ids': ['Informe todos os IDs desta versão, sem duplicações ou IDs externos.']})
    items = [mapping[pk] for pk in ids]
    persist_order(items)
    return items
