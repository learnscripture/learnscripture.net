from django.dispatch import Signal

# Sent when a user joins a group.
# - sender = Group object
# - account = Account object
group_joined = Signal()

# Sent when an invitation is created.
# - sender = Invitation object
invitation_created = Signal()


# Sent when a public group is created, or made public
# - sender = Group object
public_group_created = Signal()
