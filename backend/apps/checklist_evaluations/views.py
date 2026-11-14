from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.reference_architectures.permissions import accessible_architectures
from apps.checklists.permissions import accessible_checklists
from .models import EvaluationParticipant
from .permissions import accessible_evaluations, require_creator
from . import serializers as schema
from . import services


def evaluation_queryset(user):
    return accessible_evaluations(user).select_related('ra_version__reference_architecture', 'checklist_version__checklist').prefetch_related(
        Prefetch('participants', queryset=EvaluationParticipant.objects.select_related('user').prefetch_related('stakeholder_roles')))


def evaluation_for(request, pk):
    return get_object_or_404(evaluation_queryset(request.user), pk=pk)


def detail_response(request, pk, status=200):
    return Response(schema.EvaluationDetailSerializer(evaluation_for(request, pk), context={'request': request}).data, status=status)


class EvaluationListView(APIView):
    def get(self, request):
        return Response(schema.EvaluationSummarySerializer(evaluation_queryset(request.user), many=True, context={'request': request}).data)

    def post(self, request):
        serializer = schema.VersionsInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        evaluation = services.create_evaluation(user=request.user, **serializer.validated_data)
        return detail_response(request, evaluation.pk, status=201)


class EvaluationDetailView(APIView):
    def get(self, request, pk):
        return detail_response(request, pk)

    def patch(self, request, pk):
        evaluation = evaluation_for(request, pk)
        require_creator(evaluation, request.user)
        serializer = schema.VersionsInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        services.update_versions(user=request.user, evaluation=evaluation, data=serializer.validated_data)
        return detail_response(request, pk)


class ParticipantListView(APIView):
    def get(self, request, pk):
        evaluation = evaluation_for(request, pk)
        participants = evaluation.participants.all()
        if evaluation.created_by_user_id != request.user.pk:
            participants = [participant for participant in participants if participant.user_id == request.user.pk]
        return Response(schema.ParticipantSerializer(participants, many=True).data)

    def post(self, request, pk):
        evaluation = evaluation_for(request, pk)
        require_creator(evaluation, request.user)
        serializer = schema.ParticipantInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = services.save_participant(user=request.user, evaluation=evaluation, **serializer.validated_data)
        return Response(schema.ParticipantSerializer(participant).data, status=201)


class ParticipantDetailView(APIView):
    def patch(self, request, pk, participant_id):
        evaluation = evaluation_for(request, pk)
        require_creator(evaluation, request.user)
        participant = get_object_or_404(evaluation.participants, pk=participant_id)
        serializer = schema.RolesInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = services.save_participant(user=request.user, evaluation=evaluation, participant=participant, **serializer.validated_data)
        return Response(schema.ParticipantSerializer(participant).data)

    def delete(self, request, pk, participant_id):
        evaluation = evaluation_for(request, pk)
        require_creator(evaluation, request.user)
        participant = get_object_or_404(evaluation.participants, pk=participant_id)
        services.remove_participant(user=request.user, evaluation=evaluation, participant=participant)
        return Response(status=204)


class StartView(APIView):
    def post(self, request, pk):
        evaluation = evaluation_for(request, pk)
        require_creator(evaluation, request.user)
        serializer = schema.EmptyInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.start_evaluation(user=request.user, evaluation=evaluation)
        return Response({'id': result.pk, 'status': result.status})


class ChoicesView(APIView):
    def get(self, request):
        # Only selection metadata, not a catalog, structure, user directory or membership list.
        architectures = accessible_architectures(request.user).prefetch_related('versions')
        checklists = accessible_checklists(request.user).prefetch_related('versions')
        def selection(item):
            return {'id': item.pk, 'name': item.name, 'visibility': item.visibility,
                    'versions': [{'id': version.pk, 'version': version.version} for version in item.versions.all()]}
        return Response({'architectures': [selection(item) for item in architectures],
                         'checklists': [selection(item) for item in checklists]})


class MyQuestionsView(APIView):
    def get(self, request, pk):
        from .models import Answer
        from .permissions import participant_for, require_in_progress, available_questions

        participant = participant_for(request.user, pk)
        evaluation = participant.checklist_evaluation
        require_in_progress(evaluation)
        questions = list(available_questions(participant).select_related('section').prefetch_related(
            'options', Prefetch('answers', queryset=Answer.objects.filter(evaluation_participant=participant), to_attr='own_answers')))
        return Response({
            'evaluation': {'id': evaluation.pk, 'status': evaluation.status,
                'ra_version': {'version': evaluation.ra_version.version, 'architecture_name': evaluation.ra_version.reference_architecture.name},
                'checklist_version': {'version': evaluation.checklist_version.version, 'checklist_name': evaluation.checklist_version.checklist.name}},
            'participant': {'name': request.user.name, 'stakeholder_roles': schema.RoleSerializer(participant.stakeholder_roles.all(), many=True).data},
            'questions': schema.MyQuestionSerializer(questions, many=True).data,
            'progress': {'answered': sum(bool(question.own_answers) for question in questions), 'total': len(questions)},
        })


class MyAnswerView(APIView):
    def put(self, request, pk, question_id):
        serializer = schema.AnswerInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        answer = services.save_answer(user=request.user, evaluation_id=pk, question_id=question_id, data=serializer.validated_data)
        return Response(schema.AnswerSerializer(answer).data)


class ProgressView(APIView):
    def get(self, request, pk):
        return Response(services.evaluation_progress(user=request.user, evaluation=evaluation_for(request, pk)))


class CompleteView(APIView):
    def post(self, request, pk):
        evaluation = evaluation_for(request, pk)
        require_creator(evaluation, request.user)
        serializer = schema.CompleteInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.complete_evaluation(user=request.user, evaluation=evaluation, **serializer.validated_data)
        return Response({'id': result.pk, 'status': result.status})


class ResultsView(APIView):
    def get(self, request, pk):
        return Response(services.evaluation_results(user=request.user, evaluation=evaluation_for(request, pk)))
