from django.dispatch import Signal

new_account = Signal()
verse_started = Signal()
verse_tested = Signal()
points_increase = Signal() # sender=account, previous_points, points_added
scored_100_percent = Signal()
