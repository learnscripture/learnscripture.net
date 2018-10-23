# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-10-23 07:52
from __future__ import unicode_literals

import re

import pyquery
from django.db import migrations


def forwards(apps, schema_editor):
    # Data fixup. We have to use real models. This code should be deleted when
    # squashing migrations.
    from awards.models import Award
    from awards.hooks import new_award_msg_html

    Notice = apps.get_model('accounts.Notice')
    Account = apps.get_model('accounts.Account')

    for notice in Notice.objects.all().filter(message_html__contains="data-award-id"):
        d = pyquery.PyQuery(notice.message_html)
        award_id = int(d.find('[data-award-id]')[0].attrib['data-award-id'])
        try:
            award = Award.objects.get(id=award_id)
        except Award.DoesNotExist:
            # An old, temporary award (reigning weekly champion), we don't care about rewriting the data anyway
            print("Skipping rewrite:")
            print(notice.id, notice.message_html)

            continue

        account_username = d.find('[data-account-username]')[0].attrib['data-account-username']
        account = Account.objects.get(username=account_username)
        if 'Points bonus' in notice.message_html:
            m = re.search(r'Points bonus: (\d+)', notice.message_html)
            points = int(m.groups()[0])
        else:
            points = None

        notice.message_html = new_award_msg_html(award, account, points=points)
        notice.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_remove_identity_new_learn_page'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
