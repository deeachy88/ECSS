# Generated by Django 4.2.6 on 2025-05-11 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecs_admin', '0003_t_village_master_village_name_dzo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_other_details',
            name='document_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
