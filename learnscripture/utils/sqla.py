from aldjemy.core import get_engine

from accounts.models import Account, Identity
from bibleverses.models import UserVerseStatus
from scores.models import ActionLog, TotalScore

default_engine = get_engine()

scores_actionlog = ActionLog.sa.table
scores_totalscore = TotalScore.sa.table
accounts_account = Account.sa.table
accounts_identity = Identity.sa.table
bibleverses_userversestatus = UserVerseStatus.sa.table
