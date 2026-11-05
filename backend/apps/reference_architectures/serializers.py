from rest_framework import serializers
from .models import ReferenceArchitecture, RAVersion
from .permissions import member_role


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
