# Generated by Django 2.2 on 2023-07-09 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0011_remove_t_workflow_dtls_dzongkhag_thromde_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='tor_approve_date',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='tor_remarks',
            field=models.CharField(blank=True, default=None, max_length=250, null=True),
        ),
    ]