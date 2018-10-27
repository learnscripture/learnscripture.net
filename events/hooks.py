from django.dispatch import receiver

import events.tasks
from accounts.signals import catechism_started, new_account, points_increase, verse_finished, verse_started
from awards.signals import new_award
from bibleverses.signals import public_verse_set_created, verse_set_chosen
from comments.signals import new_comment
from groups.signals import group_joined, public_group_created


@receiver(new_award)
def new_award_receiver(sender, **kwargs):
    award = sender
    events.tasks.create_award_received_event.delay(award.id)


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender=None, chosen_by=None, **kwargs):
    verse_set = sender
    chosen_by_id = None if chosen_by is None else chosen_by.id
    events.tasks.create_started_verse_set_event.apply_async([verse_set.id, chosen_by_id],
                                                            countdown=5)


@receiver(new_account)
def new_account_receiver(sender, **kwargs):
    account = sender
    events.tasks.create_new_account_event.apply_async([account.id], countdown=5)


@receiver(verse_started)
def verse_started_receiver(sender, **kwargs):
    account = sender
    events.tasks.create_verses_started_milestone_event.apply_async([account.id],
                                                                   countdown=2)


@receiver(verse_finished)
def verse_finished_receiver(sender, **kwargs):
    account = sender
    events.tasks.create_verses_finished_milestone_event.apply_async([account.id],
                                                                    countdown=2)


@receiver(catechism_started)
def catechism_started_receiver(sender, **kwargs):
    account = sender
    catechism = kwargs['catechism']
    events.tasks.create_started_catechism_event.apply_async([account.id,
                                                             catechism.id],
                                                            countdown=2)


@receiver(points_increase)
def points_increase_receiver(sender=None, previous_points=None, points_added=None, **kwargs):
    account = sender
    events.tasks.create_points_milestone_event.apply_async([account.id,
                                                           previous_points,
                                                           points_added],
                                                           countdown=5)


@receiver(public_verse_set_created)
def public_verse_set_created_receiver(sender, **kwargs):
    verse_set = sender
    events.tasks.create_new_verse_set_event.apply_async([verse_set.id],
                                                        countdown=5)


@receiver(group_joined)
def group_joined_receiver(sender, account=None, **kwargs):
    group = sender
    events.tasks.create_group_joined_event.apply_async([group.id, account.id],
                                                       countdown=5)


@receiver(public_group_created)
def public_group_created_receiver(sender, **kwargs):
    group = sender
    events.tasks.create_group_created_event.apply_async([group.id],
                                                        countdown=5)


@receiver(new_comment)
def new_comment_receiver(sender, **kwargs):
    comment = sender
    events.tasks.create_new_comment_event.apply_async([comment.id],
                                                      countdown=5)
