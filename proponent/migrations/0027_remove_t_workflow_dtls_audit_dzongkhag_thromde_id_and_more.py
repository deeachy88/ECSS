# Generated by Django 4.2.6 on 2024-03-24 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0026_rename_record_id_t_ec_industries_t1_general_record_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='t_workflow_dtls_audit',
            name='dzongkhag_thromde_id',
        ),
        migrations.AddField(
            model_name='t_workflow_dtls_audit',
            name='application_source',
            field=models.CharField(blank=True, default=None, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='t_workflow_dtls_audit',
            name='application_status',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]
