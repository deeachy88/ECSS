# Generated by Django 2.2 on 2023-07-06 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0010_auto_20230623_0747'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='t_workflow_dtls',
            name='dzongkhag_thromde_id',
        ),
    ]