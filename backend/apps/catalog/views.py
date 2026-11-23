from django.db.models import Count
from django.db.models.functions import Lower
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.checklists.models import Checklist
from apps.reference_architectures.models import ReferenceArchitecture
from .serializers import CatalogQuery, ArchitectureListing, ChecklistListing


class CatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repeated = [key for key in request.query_params if len(request.query_params.getlist(key)) != 1]
        if repeated:
            raise ValidationError({key: ['Informe este parâmetro apenas uma vez.'] for key in repeated})
        query = CatalogQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        kind, term = query.validated_data['type'], query.validated_data['q']
        model, serializer = (ReferenceArchitecture, ArchitectureListing) if kind == 'ra' else (Checklist, ChecklistListing)
        # Catalog visibility is deliberately narrower than accessible_* (which include private ownership/membership).
        items = model.objects.filter(visibility='PUBLIC', name__icontains=term).annotate(
            version_count=Count('versions')).order_by(Lower('name'), 'name', 'id')
        return Response(serializer(items, many=True).data)
