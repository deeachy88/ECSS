# Generated by Django 4.2.6 on 2024-10-10 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_payment_details',
            name='service_type',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
    ]
