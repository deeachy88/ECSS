# Generated by Django 2.2 on 2023-07-17 21:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0014_auto_20230717_1932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='t_ec_industries_t1_general',
            name='tor_approve_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
