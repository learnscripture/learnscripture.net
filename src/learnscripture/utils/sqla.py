from aldjemy.core import get_engine

from accounts.models import Account, Identity
from bibleverses.models import UserVerseStatus
from scores.models import ActionLog, TotalScore

default_engine = get_engine()

get_scores_actionlog = lambda: ActionLog.sa.__table__
get_scores_totalscore = lambda: TotalScore.sa.__table__
get_accounts_account = lambda: Account.sa.__table__
get_accounts_identity = lambda: Identity.sa.__table__
get_bibleverses_userversestatus = lambda: UserVerseStatus.sa.__table__
