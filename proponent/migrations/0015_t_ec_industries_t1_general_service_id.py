# Generated by Django 4.1.3 on 2023-03-29 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proponent', '0014_t_ec_industries_t11_ec_details_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='t_ec_industries_t1_general',
            name='service_id',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]