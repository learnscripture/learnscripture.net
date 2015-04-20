from django.dispatch import Signal

donation_drive_contributed_to = Signal()  # sender=DonationDrive
target_reached = Signal()  # sender=DonationDrive
