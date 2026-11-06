from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import ReferenceArchitecture, ReferenceArchitectureMember, ArchitecturalElementType


def accessible_architectures(user):
    return ReferenceArchitecture.objects.filter(Q(visibility='PUBLIC') | Q(members__user=user)).distinct()


def member_role(architecture, user):
    return architecture.members.filter(user=user).values_list('role', flat=True).first()


def require_role(architecture, user, *, owner_only=False):
    allowed = [ReferenceArchitectureMember.Role.OWNER] if owner_only else ReferenceArchitectureMember.Role.values
    if member_role(architecture, user) not in allowed:
        raise PermissionDenied('Você não tem permissão para realizar esta operação.')


def available_element_types(user, architecture=None):
    available = Q(created_by_user__isnull=True) | Q(created_by_user=user)
    if architecture is not None and member_role(architecture, user):
        available |= Q(ra_elements__ra_version__reference_architecture=architecture)
    return ArchitecturalElementType.objects.filter(available).distinct()
