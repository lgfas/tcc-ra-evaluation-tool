from rest_framework import serializers
from apps.checklists.serializers import StrictInputSerializer, SectionSerializer, OptionSerializer
from apps.checklists.models import StakeholderRole, Question
from apps.checklists.permissions import accessible_checklists
from apps.reference_architectures.permissions import accessible_architectures
from .models import ChecklistEvaluation, EvaluationParticipant, Answer


class VersionsInput(StrictInputSerializer):
    ra_version_id = serializers.IntegerField(min_value=1)
    checklist_version_id = serializers.IntegerField(min_value=1)


class RolesInput(StrictInputSerializer):
    stakeholder_role_ids = serializers.ListField(child=serializers.IntegerField(min_value=1))


class ParticipantInput(RolesInput):
    email = serializers.EmailField(max_length=254)


class EmptyInput(StrictInputSerializer):
    pass


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StakeholderRole
        fields = ['id', 'name']


class ParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    stakeholder_roles = RoleSerializer(many=True, read_only=True)

    def get_user(self, obj):
        return {'id': obj.user_id, 'name': obj.user.name, 'email': obj.user.email}

    class Meta:
        model = EvaluationParticipant
        fields = ['id', 'user', 'stakeholder_roles']


class EvaluationSummarySerializer(serializers.ModelSerializer):
    ra_version = serializers.SerializerMethodField()
    checklist_version = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    is_participant = serializers.SerializerMethodField()
    can_configure = serializers.SerializerMethodField()

    def get_ra_version(self, obj):
        version = obj.ra_version
        return {'id': version.pk, 'version': version.version, 'architecture_id': version.reference_architecture_id,
                'architecture_name': version.reference_architecture.name}

    def get_checklist_version(self, obj):
        version = obj.checklist_version
        return {'id': version.pk, 'version': version.version, 'checklist_id': version.checklist_id,
                'checklist_name': version.checklist.name}

    def get_is_creator(self, obj):
        return obj.created_by_user_id == self.context['request'].user.pk

    def get_is_participant(self, obj):
        return any(participant.user_id == self.context['request'].user.pk for participant in obj.participants.all())

    def get_can_configure(self, obj):
        return self.get_is_creator(obj) and obj.status == ChecklistEvaluation.Status.DRAFT

    class Meta:
        model = ChecklistEvaluation
        fields = ['id', 'ra_version', 'checklist_version', 'status', 'created_at', 'is_creator', 'is_participant', 'can_configure']


class EvaluationDetailSerializer(EvaluationSummarySerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        user = self.context['request'].user
        own = next((participant for participant in obj.participants.all() if participant.user_id == user.pk), None)
        data['own_participation'] = ParticipantSerializer(own).data if own else None
        if self.get_is_creator(obj):
            data['participants'] = ParticipantSerializer(obj.participants.all(), many=True).data
            can_read_checklist = accessible_checklists(user).filter(pk=obj.checklist_version.checklist_id).exists()
            can_read_ra = accessible_architectures(user).filter(pk=obj.ra_version.reference_architecture_id).exists()
            data['artifacts_accessible'] = can_read_ra and can_read_checklist
            data['question_count'] = obj.checklist_version.questions.count() if can_read_checklist else None
            data['available_stakeholders'] = RoleSerializer(obj.checklist_version.stakeholders.all(), many=True).data if (
                can_read_checklist and obj.status == ChecklistEvaluation.Status.DRAFT) else []
        return data


class AnswerInput(StrictInputSerializer):
    response_option_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    text_value = serializers.CharField(required=False, allow_blank=True, default='', trim_whitespace=False)
    comment = serializers.CharField(required=False, allow_blank=True, default='', trim_whitespace=False)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'response_option_id', 'text_value', 'comment']
        read_only_fields = fields


class MyQuestionSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    options = OptionSerializer(many=True, read_only=True)
    answer = serializers.SerializerMethodField()

    def get_answer(self, obj):
        answers = obj.own_answers
        return AnswerSerializer(answers[0]).data if answers else None

    class Meta:
        model = Question
        fields = ['id', 'statement', 'response_type', 'comment_mode', 'section', 'order_index', 'options', 'answer']
