# Generated by Django 4.2.6 on 2024-06-17 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecs_admin', '0014_rename_dzongkhag_serial_no_t_dzongkhag_master_dzongkhag_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_user_master',
            name='employee_id',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
    ]