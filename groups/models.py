from autoslug import AutoSlugField
from django.db import models
from django.db.models import Count
from django.utils import timezone

from accounts.models import Account
from learnscripture.datastructures import make_choices


class GroupManager(models.Manager):

    def visible_for_account(self, account):
        groups = Group.objects.all()
        public_groups = groups.filter(public=True)
        visible_groups = public_groups

        if account is not None:
            account_groups = groups.filter(members=account)
            visible_groups = visible_groups | account_groups

            invited_groups = groups.filter(invitations__account=account)
            visible_groups = visible_groups | invited_groups

            created_groups = groups.filter(created_by=account)
            visible_groups = visible_groups | created_groups

        return visible_groups.distinct()


class Group(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', unique=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(Account, related_name='groups_created')
    public = models.BooleanField()
    open = models.BooleanField()
    members = models.ManyToManyField(Account, through='Membership',
                                     related_name='groups')


    def can_join(self, account):
        if self.open:
            return True
        if self.created_by == account:
            return True
        if self.invitations.filter(account=account).exists():
            return True
        return False


    objects = GroupManager()

    def __unicode__(self):
        return self.name


class Membership(models.Model):
    account = models.ForeignKey(Account, related_name='memberships')
    group = models.ForeignKey(Group, related_name='memberships')

    created = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u'Membership of %s by %s' % (self.group, self.account)


class InvitationManager(models.Manager):
    def get_query_set(self):
        return super(InvitationManager, self).get_query_set().select_related('account', 'group', 'created_by')

class Invitation(models.Model):
    account = models.ForeignKey(Account, related_name='invitations')
    group = models.ForeignKey(Group, related_name='invitations')
    created_by = models.ForeignKey(Account, related_name='invitations_created')

    objects = InvitationManager()

    def __unicode__(self):
        return u'Invitation to %s for %s from %s' % (self.group, self.account, self.created_by)
