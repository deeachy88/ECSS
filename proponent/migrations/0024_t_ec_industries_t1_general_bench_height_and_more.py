# Generated by Django 4.2.6 on 2023-12-09 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0023_t_ec_industries_t1_general_alternative_adequate_justification_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='bench_height',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='bench_width',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='production_capacity',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='stripping_ratio',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]