from typing import ClassVar

from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in ("READ_ONLY", "USER", "ADMIN"):
        Group.objects.using(schema_editor.connection.alias).get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies: ClassVar = [("music", "0001_initial")]
    operations: ClassVar = [
        migrations.RunPython(create_roles, migrations.RunPython.noop)
    ]
