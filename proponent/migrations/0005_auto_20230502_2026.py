# Generated by Django 2.2 on 2023-05-02 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0004_t_ec_industries_t1_general_additional_info_letter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_workflow_dtls',
            name='application_status',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]
