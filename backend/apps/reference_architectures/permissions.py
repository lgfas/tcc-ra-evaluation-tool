from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import ReferenceArchitecture, ReferenceArchitectureMember


def accessible_architectures(user):
    return ReferenceArchitecture.objects.filter(Q(visibility='PUBLIC') | Q(members__user=user)).distinct()


def member_role(architecture, user):
    return architecture.members.filter(user=user).values_list('role', flat=True).first()


def require_role(architecture, user, *, owner_only=False):
    allowed = [ReferenceArchitectureMember.Role.OWNER] if owner_only else ReferenceArchitectureMember.Role.values
    if member_role(architecture, user) not in allowed:
        raise PermissionDenied('Você não tem permissão para realizar esta operação.')
