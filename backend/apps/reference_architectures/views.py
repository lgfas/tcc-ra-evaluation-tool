from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ReferenceArchitecture
from .permissions import accessible_architectures, require_role, available_element_types
from .serializers import (ArchitectureSerializer, ArchitectureDetailSerializer, CreateArchitectureSerializer,
                          MetadataSerializer, VersionInputSerializer, VersionSerializer,
                          ElementSerializer, ElementInputSerializer, ElementTypeSerializer, ElementTypeQuerySerializer)
from .services import create_reference_architecture, create_version, create_element, update_element


def architecture_for(request, pk):
    return get_object_or_404(accessible_architectures(request.user).annotate(version_count=Count('versions', distinct=True)), pk=pk)


class ArchitectureListView(APIView):
    def get(self, request):
        architectures = ReferenceArchitecture.objects.filter(members__user=request.user).annotate(version_count=Count('versions'))
        return Response(ArchitectureSerializer(architectures, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = CreateArchitectureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        architecture = create_reference_architecture(user=request.user, **serializer.validated_data)
        return Response(ArchitectureDetailSerializer(architecture_for(request, architecture.pk), context={'request': request}).data, status=201)


class ArchitectureDetailView(APIView):
    def get(self, request, pk):
        return Response(ArchitectureDetailSerializer(architecture_for(request, pk), context={'request': request}).data)

    def patch(self, request, pk):
        architecture = architecture_for(request, pk)
        require_role(architecture, request.user, owner_only=True)
        serializer = MetadataSerializer(architecture, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ArchitectureDetailSerializer(architecture, context={'request': request}).data)


class VersionListView(APIView):
    def get(self, request, pk):
        return Response(VersionSerializer(architecture_for(request, pk).versions.all(), many=True).data)

    def post(self, request, pk):
        architecture = architecture_for(request, pk)
        require_role(architecture, request.user)
        serializer = VersionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = create_version(architecture=architecture, **serializer.validated_data)
        return Response(VersionSerializer(version).data, status=201)


class VersionDetailView(APIView):
    def get(self, request, pk, version_id):
        version = get_object_or_404(architecture_for(request, pk).versions, pk=version_id)
        return Response(VersionSerializer(version).data)


def version_for(request, pk, version_id):
    return get_object_or_404(architecture_for(request, pk).versions.select_related('reference_architecture'), pk=version_id)


class ElementListView(APIView):
    def get(self, request, pk, version_id):
        version = version_for(request, pk, version_id)
        return Response(ElementSerializer(version.elements.select_related('element_type'), many=True).data)

    def post(self, request, pk, version_id):
        version = version_for(request, pk, version_id)
        require_role(version.reference_architecture, request.user)
        serializer = ElementInputSerializer(data=request.data, context={'request': request, 'architecture': version.reference_architecture})
        serializer.is_valid(raise_exception=True)
        element = create_element(user=request.user, version=version, data=serializer.validated_data)
        return Response(ElementSerializer(element).data, status=201)


class ElementDetailView(APIView):
    def get_element(self, request, pk, version_id, element_id):
        version = version_for(request, pk, version_id)
        return get_object_or_404(version.elements.select_related('element_type', 'ra_version__reference_architecture'), pk=element_id)

    def get(self, request, pk, version_id, element_id):
        return Response(ElementSerializer(self.get_element(request, pk, version_id, element_id)).data)

    def patch(self, request, pk, version_id, element_id):
        element = self.get_element(request, pk, version_id, element_id)
        architecture = element.ra_version.reference_architecture
        require_role(architecture, request.user)
        serializer = ElementInputSerializer(data=request.data, partial=True, context={'request': request, 'architecture': architecture})
        serializer.is_valid(raise_exception=True)
        element = update_element(user=request.user, element=element, data=serializer.validated_data)
        return Response(ElementSerializer(element).data)


class ElementTypeListView(APIView):
    def get(self, request):
        architecture = None
        architecture_id = request.query_params.get('reference_architecture_id')
        if architecture_id is not None:
            query = ElementTypeQuerySerializer(data=request.query_params)
            query.is_valid(raise_exception=True)
            architecture = architecture_for(request, query.validated_data['reference_architecture_id'])
        return Response(ElementTypeSerializer(available_element_types(request.user, architecture), many=True).data)

    def post(self, request):
        serializer = ElementTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by_user=request.user)
        return Response(serializer.data, status=201)
