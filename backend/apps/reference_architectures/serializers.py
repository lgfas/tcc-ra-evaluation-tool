from rest_framework import serializers
from .models import ReferenceArchitecture, RAVersion, ArchitecturalElementType, RAElement
from .permissions import member_role, available_element_types


class VersionInputSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=100)
    description_markdown = serializers.CharField(trim_whitespace=False)


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAVersion
        fields = ['id', 'version', 'description_markdown', 'created_at']
        read_only_fields = fields


class MetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceArchitecture
        fields = ['name', 'visibility']


class CreateArchitectureSerializer(MetadataSerializer):
    initial_version = VersionInputSerializer()

    class Meta(MetadataSerializer.Meta):
        fields = ['name', 'visibility', 'initial_version']


class ArchitectureSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    version_count = serializers.IntegerField(read_only=True)

    def get_role(self, obj):
        return member_role(obj, self.context['request'].user)

    class Meta:
        model = ReferenceArchitecture
        fields = ['id', 'name', 'visibility', 'role', 'version_count']


class ArchitectureDetailSerializer(ArchitectureSerializer):
    versions = VersionSerializer(many=True, read_only=True)

    class Meta(ArchitectureSerializer.Meta):
        fields = ArchitectureSerializer.Meta.fields + ['versions']


class ElementTypeQuerySerializer(serializers.Serializer):
    reference_architecture_id = serializers.IntegerField(min_value=1, max_value=9223372036854775807)


class ElementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitecturalElementType
        fields = ['id', 'name']
        read_only_fields = ['id']


class ElementInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description_markdown = serializers.CharField(trim_whitespace=False)
    element_type_id = serializers.PrimaryKeyRelatedField(source='element_type', queryset=ArchitecturalElementType.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['element_type_id'].queryset = available_element_types(
            self.context['request'].user, self.context['architecture'])

    def validate(self, attrs):
        if 'ra_version' in self.initial_data or 'ra_version_id' in self.initial_data:
            raise serializers.ValidationError({'ra_version': ['Não é permitido transferir um elemento entre versões.']})
        return attrs


class ElementSerializer(serializers.ModelSerializer):
    element_type = ElementTypeSerializer(read_only=True)

    class Meta:
        model = RAElement
        fields = ['id', 'name', 'description_markdown', 'element_type']
        read_only_fields = fields
