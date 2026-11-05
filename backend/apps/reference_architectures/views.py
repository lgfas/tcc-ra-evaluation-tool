from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ReferenceArchitecture
from .permissions import accessible_architectures, require_role
from .serializers import (ArchitectureSerializer, ArchitectureDetailSerializer, CreateArchitectureSerializer,
                          MetadataSerializer, VersionInputSerializer, VersionSerializer)
from .services import create_reference_architecture, create_version


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
