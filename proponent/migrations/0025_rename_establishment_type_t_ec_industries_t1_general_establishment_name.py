# Generated by Django 4.2.6 on 2024-01-19 10:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0024_t_ec_industries_t1_general_bench_height_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='t_ec_industries_t1_general',
            old_name='establishment_type',
            new_name='establishment_name',
        ),
    ]