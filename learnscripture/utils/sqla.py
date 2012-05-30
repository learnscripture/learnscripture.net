from django.conf import settings
from sqlalchemy.schema import MetaData, Table
from sqlalchemy import create_engine

default_engine = create_engine('postgresql://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s'
                               % settings.DATABASES['default'])
metadata = MetaData()

def t(n):
    return Table(n, metadata, autoload=True, autoload_with=default_engine)

scores_scorelog = t('scores_scorelog')
scores_totalscore = t('scores_totalscore')
accounts_account = t('accounts_account')
bibleverses_userversestatus = t('bibleverses_userversestatus')
