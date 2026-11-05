from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from .models import ReferenceArchitecture, ReferenceArchitectureMember, RAVersion


@transaction.atomic
def create_reference_architecture(*, user, initial_version, **metadata):
    architecture = ReferenceArchitecture.objects.create(**metadata)
    ReferenceArchitectureMember.objects.create(reference_architecture=architecture, user=user,
                                               role=ReferenceArchitectureMember.Role.OWNER)
    RAVersion.objects.create(reference_architecture=architecture, **initial_version)
    return architecture


def create_version(*, architecture, **data):
    try:
        with transaction.atomic():
            return RAVersion.objects.create(reference_architecture=architecture, **data)
    except IntegrityError as exc:
        if getattr(exc.__cause__, 'diag', None) and exc.__cause__.diag.constraint_name == 'ra_unique_version':
            raise ValidationError({'version': ['Já existe uma versão com este identificador nesta RA.']}) from exc
        raise
