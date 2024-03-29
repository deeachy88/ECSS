# Generated by Django 4.2.6 on 2024-03-26 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecs_admin', '0013_remove_t_dzongkhag_master_dzongkhag_name_bh_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='t_dzongkhag_master',
            old_name='dzongkhag_serial_no',
            new_name='dzongkhag_code',
        ),
        migrations.RenameField(
            model_name='t_gewog_master',
            old_name='gewog_serial_no',
            new_name='gewog_code',
        ),
        migrations.RenameField(
            model_name='t_village_master',
            old_name='village_serial_no',
            new_name='village_code',
        ),
        migrations.RemoveField(
            model_name='t_dzongkhag_master',
            name='dzongkhag_id',
        ),
        migrations.RemoveField(
            model_name='t_gewog_master',
            name='dzongkhag_serial_no',
        ),
        migrations.RemoveField(
            model_name='t_gewog_master',
            name='gewog_id',
        ),
        migrations.RemoveField(
            model_name='t_village_master',
            name='gewog_serial_no',
        ),
        migrations.RemoveField(
            model_name='t_village_master',
            name='village_id',
        ),
        migrations.AddField(
            model_name='t_gewog_master',
            name='dzongkhag_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ecs_admin.t_dzongkhag_master'),
        ),
        migrations.AddField(
            model_name='t_village_master',
            name='gewog_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ecs_admin.t_gewog_master'),
        ),
        migrations.AddField(
            model_name='t_village_master',
            name='village_name_dzo',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='t_dzongkhag_master',
            name='dzongkhag_name',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='t_gewog_master',
            name='gewog_name',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='t_village_master',
            name='village_name',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
    ]
