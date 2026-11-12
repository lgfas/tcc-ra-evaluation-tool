from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Checklist, ChecklistSection, StakeholderRole, Question
from .permissions import accessible_checklists, require_owner
from . import serializers as schema
from . import services


def checklist_for(request, pk):
    return get_object_or_404(accessible_checklists(request.user).annotate(version_count=Count('versions')), pk=pk)


def version_for(request, pk, version_id):
    return get_object_or_404(checklist_for(request, pk).versions.select_related('checklist'), pk=version_id)


def questions_for(version):
    return version.questions.select_related('section').prefetch_related('stakeholders', 'options')


def checklist_response(request, pk, status=200):
    return Response(schema.ChecklistDetailSerializer(checklist_for(request, pk), context={'request': request}).data, status=status)


class ChecklistListView(APIView):
    def get(self, request):
        items = Checklist.objects.filter(owner_user=request.user).annotate(version_count=Count('versions'))
        return Response(schema.ChecklistSerializer(items, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = schema.CreateChecklistInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = services.create_checklist(user=request.user, **serializer.validated_data)
        return checklist_response(request, item.pk, status=201)


class ChecklistDetailView(APIView):
    def get(self, request, pk):
        return checklist_response(request, pk)

    def patch(self, request, pk):
        item = checklist_for(request, pk)
        require_owner(item, request.user)
        serializer = schema.MetadataInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        services.update_checklist(user=request.user, checklist=item, data=serializer.validated_data)
        return checklist_response(request, pk)


class VersionListView(APIView):
    def get(self, request, pk):
        return Response(schema.VersionSerializer(checklist_for(request, pk).versions.all(), many=True).data)

    def post(self, request, pk):
        item = checklist_for(request, pk)
        require_owner(item, request.user)
        serializer = schema.VersionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = services.create_version(user=request.user, checklist=item, **serializer.validated_data)
        return Response(schema.VersionSerializer(version).data, status=201)


class VersionDetailView(APIView):
    def get(self, request, pk, version_id):
        return Response(schema.VersionSerializer(version_for(request, pk, version_id)).data)


class StructureListView(APIView):
    def queryset(self, version):
        return self.model.objects.filter(checklist_version=version)

    def get(self, request, pk, version_id):
        version = version_for(request, pk, version_id)
        return Response(self.output(self.queryset(version), many=True).data)

    def post(self, request, pk, version_id):
        version = version_for(request, pk, version_id)
        require_owner(version.checklist, request.user)
        serializer = self.input(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.save(user=request.user, version=version, data=serializer.validated_data)
        return Response(self.output(instance).data, status=201)


class StructureDetailView(APIView):
    def patch(self, request, pk, version_id, item_id):
        version = version_for(request, pk, version_id)
        require_owner(version.checklist, request.user)
        instance = get_object_or_404(self.model, pk=item_id, checklist_version=version)
        serializer = self.input(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = self.save(user=request.user, version=version, instance=instance, data=serializer.validated_data)
        return Response(self.output(instance).data)


class SectionListView(StructureListView):
    model = ChecklistSection
    input = schema.SectionInput
    output = schema.SectionSerializer
    save = staticmethod(services.save_section)


class SectionDetailView(StructureDetailView, SectionListView):
    # Only PATCH is exposed for section details.
    http_method_names = ['patch', 'options']


class StakeholderListView(StructureListView):
    model = StakeholderRole
    input = schema.StakeholderInput
    output = schema.StakeholderSerializer
    save = staticmethod(services.save_stakeholder)


class StakeholderDetailView(StructureDetailView, StakeholderListView):
    http_method_names = ['patch', 'options']


class QuestionListView(StructureListView):
    model = Question
    input = schema.QuestionInput
    output = schema.QuestionSerializer
    save = staticmethod(services.save_question)

    def queryset(self, version):
        return questions_for(version)


class QuestionDetailView(StructureDetailView, QuestionListView):
    http_method_names = ['get', 'patch', 'head', 'options']

    def get(self, request, pk, version_id, item_id):
        version = version_for(request, pk, version_id)
        return Response(self.output(get_object_or_404(questions_for(version), pk=item_id)).data)


class SectionReorderView(APIView):
    model = ChecklistSection
    output = schema.SectionSerializer

    def post(self, request, pk, version_id):
        version = version_for(request, pk, version_id)
        require_owner(version.checklist, request.user)
        serializer = schema.ReorderInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reorder(user=request.user, version=version, model=self.model, **serializer.validated_data)
        queryset = questions_for(version) if self.model is Question else version.sections.all()
        return Response(self.output(queryset, many=True).data)


class QuestionReorderView(SectionReorderView):
    model = Question
    output = schema.QuestionSerializer
