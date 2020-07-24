# -*- coding: utf-8 -*-
from django.db import models, migrations
import autoslug.fields
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
import bibleverses.fields
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QAPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference', models.CharField(max_length=100)),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('order', models.PositiveSmallIntegerField()),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'QA pair',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(unique=True, max_length=20)),
                ('slug', models.CharField(unique=True, max_length=20)),
                ('full_name', models.CharField(unique=True, max_length=255)),
                ('url', models.URLField(default='', blank=True)),
                ('text_type', models.PositiveSmallIntegerField(default=1, choices=[(1, 'Bible'), (2, 'Catechism')])),
                ('description', models.TextField(blank=True)),
                ('public', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['short_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserVerseStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference', models.CharField(max_length=100)),
                ('text_order', models.PositiveSmallIntegerField()),
                ('memory_stage', models.PositiveSmallIntegerField(default=1, choices=[(1, 'nothing'), (2, 'seen'), (3, 'tested')])),
                ('strength', models.FloatField(default=0.0)),
                ('added', models.DateTimeField()),
                ('first_seen', models.DateTimeField(null=True, blank=True)),
                ('last_tested', models.DateTimeField(null=True, blank=True)),
                ('next_test_due', models.DateTimeField(null=True, blank=True)),
                ('ignored', models.BooleanField(default=False)),
                ('for_identity', models.ForeignKey(related_name='verse_statuses', to='accounts.Identity', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'User verse statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Verse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference', models.CharField(max_length=100)),
                ('text', models.TextField(blank=True)),
                ('text_tsv', bibleverses.fields.VectorField()),
                ('book_number', models.PositiveSmallIntegerField()),
                ('chapter_number', models.PositiveSmallIntegerField()),
                ('verse_number', models.PositiveSmallIntegerField()),
                ('bible_verse_number', models.PositiveSmallIntegerField()),
                ('missing', models.BooleanField(default=False)),
                ('version', models.ForeignKey(to='bibleverses.TextVersion', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('bible_verse_number',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VerseChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reference', models.CharField(max_length=100)),
                ('set_order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VerseSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(populate_from='name', unique=True, editable=False)),
                ('description', models.TextField(blank=True)),
                ('additional_info', models.TextField(blank=True)),
                ('set_type', models.PositiveSmallIntegerField(choices=[(1, 'Selection'), (2, 'Passage')])),
                ('public', models.BooleanField(default=False)),
                ('breaks', models.TextField(default='', blank=True)),
                ('popularity', models.PositiveIntegerField(default=0)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('passage_id', models.CharField(default='', max_length=203)),
                ('created_by', models.ForeignKey(related_name='verse_sets_created', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WordSuggestionData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version_slug', models.CharField(default='', max_length=20)),
                ('reference', models.CharField(max_length=100)),
                ('hash', models.CharField(max_length=40)),
                ('suggestions',  django.contrib.postgres.fields.JSONField(default=dict)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='wordsuggestiondata',
            unique_together=set([('version_slug', 'reference')]),
        ),
        migrations.AddField(
            model_name='versechoice',
            name='verse_set',
            field=models.ForeignKey(related_name='verse_choices', to='bibleverses.VerseSet', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='versechoice',
            unique_together=set([('verse_set', 'reference')]),
        ),
        migrations.AlterUniqueTogether(
            name='verse',
            unique_together=set([('version', 'bible_verse_number'), ('version', 'reference')]),
        ),
        migrations.AddField(
            model_name='userversestatus',
            name='verse_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='bibleverses.VerseSet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userversestatus',
            name='version',
            field=models.ForeignKey(to='bibleverses.TextVersion', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='userversestatus',
            unique_together=set([('for_identity', 'verse_set', 'reference', 'version')]),
        ),
        migrations.AddField(
            model_name='qapair',
            name='catechism',
            field=models.ForeignKey(related_name='qapairs', to='bibleverses.TextVersion', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='qapair',
            unique_together=set([('catechism', 'order'), ('catechism', 'reference')]),
        ),
    ]
