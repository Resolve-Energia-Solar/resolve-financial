from django.db import migrations, models

def create_user_types(apps, schema_editor):
    UserType = apps.get_model('accounts', 'UserType')
    UserType.objects.bulk_create([
        UserType(name='Cliente', description=''),
        UserType(name='Fornecedor', description=''),
        UserType(name='Funcionário', description='')
    ])

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_branch_is_deleted_department_is_deleted_and_more'),
    ]

    operations = [
        migrations.RunPython(create_user_types),
    ]
