from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from .models import ReferenceArchitecture, ReferenceArchitectureMember, RAVersion, RAElement
from .permissions import require_role
from apps.version_protection import require_editable_version


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


def writable_version(*, user, version):
    version = RAVersion.objects.select_for_update(of=('self',)).select_related('reference_architecture').get(pk=version.pk)
    require_role(version.reference_architecture, user)
    require_editable_version(ra_version_id=version.pk)
    return version


@transaction.atomic
def create_element(*, user, version, data):
    version = writable_version(user=user, version=version)
    return RAElement.objects.create(ra_version=version, **data)


@transaction.atomic
def update_element(*, user, element, data):
    version = writable_version(user=user, version=element.ra_version)
    element = RAElement.objects.get(pk=element.pk, ra_version=version)
    for field in ('name', 'element_type', 'description_markdown'):
        if field in data:
            setattr(element, field, data[field])
    element.save()
    return element
