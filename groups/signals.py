from django.dispatch import Signal

# Sent when a user joins a group.
# - sender = Group object
# - account = Account object
group_joined = Signal()

# Sent when an invitation is created.
# - sender = Invitation object
invitation_created = Signal()
