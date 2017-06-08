# -*- coding: utf-8 -*-
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SiteNotice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message_html', models.TextField()),
                ('is_active', models.BooleanField(default=False)),
                ('begins', models.DateTimeField()),
                ('ends', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
