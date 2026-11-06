from django.conf import settings
from django.db import models


class ReferenceArchitecture(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = 'PRIVATE', 'Privada'
        PUBLIC = 'PUBLIC', 'Pública'

    name = models.CharField(max_length=255)
    visibility = models.CharField(max_length=7, choices=Visibility.choices)

    class Meta:
        ordering = ['name', 'id']
        constraints = [models.CheckConstraint(condition=models.Q(visibility__in=['PRIVATE', 'PUBLIC']), name='ra_valid_visibility')]


class ReferenceArchitectureMember(models.Model):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Proprietário'
        EDITOR = 'EDITOR', 'Editor'

    reference_architecture = models.ForeignKey(ReferenceArchitecture, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ra_memberships')
    role = models.CharField(max_length=6, choices=Role.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reference_architecture', 'user'], name='ra_unique_member'),
            models.UniqueConstraint(fields=['reference_architecture'], condition=models.Q(role='OWNER'), name='ra_unique_owner'),
            models.CheckConstraint(condition=models.Q(role__in=['OWNER', 'EDITOR']), name='ra_valid_role'),
        ]


class RAVersion(models.Model):
    reference_architecture = models.ForeignKey(ReferenceArchitecture, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=100)
    description_markdown = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.UniqueConstraint(fields=['reference_architecture', 'version'], name='ra_unique_version')]


class ArchitecturalElementType(models.Model):
    name = models.CharField(max_length=255)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                       on_delete=models.PROTECT, related_name='architectural_element_types')

    class Meta:
        ordering = ['name', 'id']


class RAElement(models.Model):
    ra_version = models.ForeignKey(RAVersion, on_delete=models.CASCADE, related_name='elements')
    element_type = models.ForeignKey(ArchitecturalElementType, on_delete=models.PROTECT, related_name='ra_elements')
    name = models.CharField(max_length=255)
    description_markdown = models.TextField()

    class Meta:
        ordering = ['name', 'id']
