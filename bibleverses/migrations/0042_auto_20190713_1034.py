# Generated by Django 2.0.10 on 2019-07-13 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bibleverses', '0041_auto_20190522_2305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verseset',
            name='passage_id',
            field=models.CharField(blank=True, default='', max_length=203),
        ),
    ]
