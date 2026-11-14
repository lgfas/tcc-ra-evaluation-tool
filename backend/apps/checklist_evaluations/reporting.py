"""Derived evaluation data. No persisted counters or fabricated missing answers."""
from collections import Counter
from .models import Answer
from .permissions import available_questions


def percentage(answered, total):
    return round(100 * answered / total, 2) if total else None


def snapshot(evaluation, *, include_values=False):
    """Caller holds the evaluation lock, shared with answer writes and completion.

    All relationships are fetched in batches, independent of participant count.
    Progress fetches only answer keys, never text or comments.
    """
    questions = list(evaluation.checklist_version.questions.select_related('section').prefetch_related('stakeholders', 'options'))
    participants = list(evaluation.participants.select_related('user', 'checklist_evaluation').prefetch_related('stakeholder_roles'))
    answer_query = Answer.objects.filter(evaluation_participant__checklist_evaluation=evaluation)
    fields = ['evaluation_participant_id', 'question_id']
    if include_values:
        fields += ['id', 'response_option_id', 'text_value', 'comment']
    answers = {(row['evaluation_participant_id'], row['question_id']): row for row in answer_query.values(*fields)}
    assignments = {participant.pk: available_questions(participant, candidates=questions) for participant in participants}
    progress = []
    for participant in participants:
        assigned = assignments[participant.pk]
        pending = [{'id': question.pk, 'statement': question.statement} for question in assigned
                   if (participant.pk, question.pk) not in answers]
        total = len(assigned)
        answered = total - len(pending)
        progress.append({'id': participant.pk, 'user': {'id': participant.user_id, 'name': participant.user.name},
            'stakeholder_roles': [{'id': role.pk, 'name': role.name} for role in participant.stakeholder_roles.all()],
            'total': total, 'answered': answered, 'pending': len(pending), 'percentage': percentage(answered, total),
            'pending_questions': pending})
    total = sum(row['total'] for row in progress)
    answered = sum(row['answered'] for row in progress)
    summary = {'participants': len(participants), 'expected': total, 'answered': answered, 'pending': total - answered,
               'percentage': percentage(answered, total),
               'participants_with_pending': sum(row['pending'] > 0 for row in progress)}
    return {'id': evaluation.pk, 'status': evaluation.status, 'totals': summary, 'participants': progress}, questions, assignments, answers


def results(evaluation):
    progress, questions, assignments, answers = snapshot(evaluation, include_values=True)
    assigned_ids = {pk: {question.pk for question in assigned} for pk, assigned in assignments.items()}
    rows = []
    for question in questions:
        responses = []
        for participant in progress['participants']:
            if question.pk not in assigned_ids[participant['id']]:
                continue
            answer = answers.get((participant['id'], question.pk))
            responses.append({'participant_id': participant['id'], 'answer': None if answer is None else {
                key: answer[key] for key in ['id', 'response_option_id', 'text_value', 'comment']}})
        valid = sum(row['answer'] is not None for row in responses)
        counts = Counter(row['answer']['response_option_id'] for row in responses if row['answer'] is not None)
        distribution = [{'id': option.pk, 'label': option.label, 'count': counts[option.pk],
                         'percentage': percentage(counts[option.pk], valid)} for option in question.options.all()]
        rows.append({'id': question.pk, 'statement': question.statement, 'response_type': question.response_type,
            'comment_mode': question.comment_mode, 'order_index': question.order_index,
            'section': {'id': question.section_id, 'name': question.section.name} if question.section_id else None,
            'stakeholder_roles': [{'id': role.pk, 'name': role.name} for role in question.stakeholders.all()],
            'expected': len(responses), 'answered': valid, 'pending': len(responses) - valid,
            'distribution': distribution, 'responses': responses})
    ra = evaluation.ra_version
    checklist = evaluation.checklist_version
    return {**progress,
        'ra_version': {'id': ra.pk, 'version': ra.version, 'architecture_name': ra.reference_architecture.name},
        'checklist_version': {'id': checklist.pk, 'version': checklist.version, 'checklist_name': checklist.checklist.name},
        'questions': rows}
