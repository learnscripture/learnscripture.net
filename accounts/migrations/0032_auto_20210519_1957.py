# Generated by Django 3.1.7 on 2021-05-19 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0031_auto_20210314_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identity',
            name='desktop_testing_method',
            field=models.CharField(choices=[('FULL_WORDS', 'Type whole word - most thorough'), ('FIRST_LETTER', 'Type first letter - faster'), ('ON_SCREEN', 'Choose from word list - recommended for  handheld devices. Only available for English translations')], default='FIRST_LETTER', max_length=20, verbose_name='Desktop testing method'),
        ),
        migrations.AlterField(
            model_name='identity',
            name='touchscreen_testing_method',
            field=models.CharField(choices=[('FULL_WORDS', 'Type whole word - most thorough'), ('FIRST_LETTER', 'Type first letter - faster'), ('ON_SCREEN', 'Choose from word list - recommended for  handheld devices. Only available for English translations')], default='FIRST_LETTER', max_length=20, verbose_name='Touchscreen testing method'),
        ),
    ]