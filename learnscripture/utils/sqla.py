from django.conf import settings
from sqlalchemy.schema import MetaData, Table
from sqlalchemy import create_engine

default_engine = create_engine('postgresql://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s'
                               % settings.DATABASES['default'])
metadata = MetaData()


scores_scorelog = Table('scores_scorelog', metadata, autoload=True, autoload_with=default_engine)
scores_totalscore = Table('scores_totalscore', metadata, autoload=True, autoload_with=default_engine)
accounts_account = Table('accounts_account', metadata, autoload=True, autoload_with=default_engine)
