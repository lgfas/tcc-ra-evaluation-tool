from rest_framework import serializers
from .models import Checklist, ChecklistVersion, ChecklistSection, StakeholderRole, Question, ResponseOption


class StrictInputSerializer(serializers.Serializer):
    """Reject relation/ownership injection instead of silently ignoring unknown keys."""
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: ['Campo não permitido.'] for key in sorted(unknown)})
        return super().to_internal_value(data)


class MetadataInput(StrictInputSerializer):
    name = serializers.CharField(max_length=255)
    origin = serializers.CharField(allow_blank=True, required=False, default='')
    visibility = serializers.ChoiceField(choices=Checklist.Visibility.choices)


class VersionInput(StrictInputSerializer):
    version = serializers.CharField(max_length=100)


class CreateChecklistInput(MetadataInput):
    initial_version = VersionInput()


class SectionInput(StrictInputSerializer):
    name = serializers.CharField(max_length=255)
    order_index = serializers.IntegerField(min_value=0, max_value=2147483647, required=False)


class StakeholderInput(StrictInputSerializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False, default='')


class OptionInput(StrictInputSerializer):
    label = serializers.CharField(max_length=255)
    order_index = serializers.IntegerField(min_value=0, max_value=2147483647)

    def validate(self, attrs):
        # Root PATCH must not make nested replacement option fields optional.
        missing = {'label', 'order_index'} - set(attrs)
        if missing:
            raise serializers.ValidationError({key: ['Este campo é obrigatório.'] for key in missing})
        return attrs

    # No IDs: supplied options replace this question's list, never another question's options.


class QuestionInput(StrictInputSerializer):
    statement = serializers.CharField()
    response_type = serializers.ChoiceField(choices=Question.ResponseType.choices)
    comment_mode = serializers.ChoiceField(choices=Question.CommentMode.choices)
    order_index = serializers.IntegerField(min_value=0, max_value=2147483647, required=False)
    section_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    stakeholder_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False)
    options = OptionInput(many=True, required=False)


class ReorderInput(StrictInputSerializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1))


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistVersion
        fields = ['id', 'version', 'created_at']


class ChecklistSerializer(serializers.ModelSerializer):
    version_count = serializers.IntegerField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    def get_can_edit(self, obj):
        return obj.owner_user_id == self.context['request'].user.pk

    class Meta:
        model = Checklist
        fields = ['id', 'owner_user', 'derived_from_checklist_version', 'name', 'origin', 'visibility', 'version_count', 'can_edit']


class ChecklistDetailSerializer(ChecklistSerializer):
    versions = VersionSerializer(many=True, read_only=True)

    class Meta(ChecklistSerializer.Meta):
        fields = ChecklistSerializer.Meta.fields + ['versions']


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistSection
        fields = ['id', 'name', 'order_index']


class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = StakeholderRole
        fields = ['id', 'name', 'description']


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseOption
        fields = ['id', 'label', 'order_index']


class QuestionSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    stakeholders = StakeholderSerializer(many=True, read_only=True)
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'statement', 'response_type', 'comment_mode', 'order_index', 'section', 'stakeholders', 'options']
