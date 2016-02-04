from sqlalchemy.schema import MetaData, Table

from aldjemy.core import get_engine

default_engine = get_engine()
metadata = MetaData()


def t(n):
    return Table(n, metadata, autoload=True, autoload_with=default_engine)

scores_actionlog = t('scores_actionlog')
scores_totalscore = t('scores_totalscore')
accounts_account = t('accounts_account')
bibleverses_userversestatus = t('bibleverses_userversestatus')
