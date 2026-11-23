from rest_framework import serializers
from apps.checklists.serializers import StrictInputSerializer
from apps.checklists.models import Checklist
from apps.reference_architectures.models import ReferenceArchitecture


class CatalogQuery(StrictInputSerializer):
    type = serializers.ChoiceField(choices=['ra', 'checklist'], error_messages={
        'required': 'Informe o tipo de artefato: ra ou checklist.',
        'invalid_choice': 'Tipo inválido. Utilize ra ou checklist.',
    })
    q = serializers.CharField(required=False, allow_blank=True, default='', max_length=255)


class ArchitectureListing(serializers.ModelSerializer):
    version_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReferenceArchitecture
        fields = ['id', 'name', 'visibility', 'version_count']


class ChecklistListing(serializers.ModelSerializer):
    version_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Checklist
        fields = ['id', 'name', 'origin', 'visibility', 'version_count']
