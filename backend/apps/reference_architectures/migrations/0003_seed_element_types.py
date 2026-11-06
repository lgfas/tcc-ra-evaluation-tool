from django.db import migrations


def seed_types(apps, schema_editor):
    element_type = apps.get_model('reference_architectures', 'ArchitecturalElementType')
    for name in ('Componente', 'Conector'):
        element_type.objects.using(schema_editor.connection.alias).get_or_create(name=name, created_by_user=None)


class Migration(migrations.Migration):
    dependencies = [('reference_architectures', '0002_architecturalelementtype_raelement')]
    operations = [migrations.RunPython(seed_types, migrations.RunPython.noop)]
