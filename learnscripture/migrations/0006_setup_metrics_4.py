# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from app_metrics.utils import create_metric
from app_metrics.models import Metric

class Migration(DataMigration):

    def forwards(self, orm):
        create_metric(name='Paying accounts', slug='accounts_paying')

    def backwards(self, orm):
        Metric.objects.filter(slug='accounts_paying').delete()


    models = {
        
    }

    complete_apps = ['learnscripture']
    symmetrical = True
