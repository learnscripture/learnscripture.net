from django.dispatch import Signal

verse_set_chosen = Signal() # sender=VerseSet, chosen_by=Account
public_verse_set_created = Signal()

