# Generated by Django 4.2.6 on 2024-06-05 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0035_t_payment_details_service_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='t_ndi_login_temp',
            fields=[
                ('record_id', models.AutoField(primary_key=True, serialize=False)),
                ('cid_number', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]