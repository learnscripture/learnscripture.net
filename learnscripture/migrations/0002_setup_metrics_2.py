import datetime

from app_metrics.utils import create_metric, metric
from app_metrics.models import Metric, MetricItem
from south.db import db
from south.v2 import DataMigration
from django.db import models

from accounts.models import Account
from scores.models import ScoreLog, ScoreReason

class Migration(DataMigration):

    def forwards(self, orm):
        create_metric(name='All requests', slug='request_all')
        create_metric(name='HTML requests', slug='request_html')
        create_metric(name='JSON requests', slug='request_json')

    def backwards(self, orm):
        pass

    models = {
    }

    complete_apps = ['learnscripture']
    symmetrical = True

    depends_on = [
        ]
