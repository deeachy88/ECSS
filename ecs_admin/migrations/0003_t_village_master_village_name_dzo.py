# Generated by Django 2.2 on 2023-05-17 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecs_admin', '0002_remove_t_village_master_village_name_dzo'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_village_master',
            name='village_name_dzo',
            field=models.CharField(default=None, max_length=100),
        ),
    ]
