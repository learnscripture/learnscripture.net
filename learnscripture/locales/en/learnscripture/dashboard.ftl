### Dashboard page

dashboard-learning-events = Learning events

dashboard-passages-youve-seen-verses-with-review-due-html =
    You've seen { $tested_total ->
            [1] 1 verse
           *[other] { $tested_total } verses
     } so far,
    <b>{ $needs_review_total } due for review</b>,
    with { $untested_total } still to start on.

dashboard-passages-youve-seen-verses =
    You've seen { $tested_total ->
            [1] 1 verse
           *[other] { $tested_total } verses
     } so far,
     with { $untested_total } still to start on.

dashboard-remember-to-create-an-account-html =
    <b>Remember to <a href="{ $signup_url }">create an account</a></b> -
    otherwise your progress will be lost! It's free, only takes a few seconds, and
    enables lots of additional features like badges, groups, leaderboards and
    statistics pages.


# Displayed as a title when there is an unfinished learning
# session that the user can continue
dashboard-continue-title =
    Continue
