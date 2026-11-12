from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import Checklist


def accessible_checklists(user):
    return Checklist.objects.filter(Q(owner_user=user) | Q(visibility=Checklist.Visibility.PUBLIC))


def require_owner(checklist, user):
    if checklist.owner_user_id != user.pk:
        raise PermissionDenied('Somente o proprietário pode modificar esta checklist.')
