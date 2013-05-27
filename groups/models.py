from autoslug import AutoSlugField
from django.db import models
from django.db.models import Count
from django.utils import timezone

from accounts.models import Account
from learnscripture.datastructures import make_choices


class GroupManager(models.Manager):

    def visible_for_account(self, account):
        groups = self.all()
        if account is None or not account.is_hellbanned:
            groups = groups.exclude(created_by__is_hellbanned=True)

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

    def editable_for_account(self, account):
        if account is None:
            return self.none()
        return self.filter(created_by=account)


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

    objects = GroupManager()

    class Meta:
        ordering = ['name']

    def can_join(self, account):
        if self.open:
            return True
        if account is None:
            return False
        if self.created_by == account:
            return True
        if self.invitations.filter(account=account).exists():
            return True
        return False

    def can_edit(self, account):
        return account == self.created_by

    def add_user(self, account):
        self.memberships.get_or_create(account=account)

    def remove_user(self, account):
        self.memberships.filter(account=account).delete()

    def invited_users(self):
        return [i.account for i in self.invitations.select_related('account')]

    @property
    def active_members(self):
        return self.members.filter(is_active=True)

    def __unicode__(self):
        return self.name

    def set_invitation_list(self, new_invited_users):
        orig_invited_users = set(self.invited_users())
        new_invited_users = set(new_invited_users)
        new_users = new_invited_users - orig_invited_users
        removed_users = orig_invited_users - new_invited_users

        self.invitations.filter(account__in=removed_users).delete()
        for u in new_users:
            if not self.created_by.is_hellbanned or u.is_hellbanned:
                # hellbanned users can't send invitations, except to
                # other hellbanned users.
                self.invitations.create(account=u,
                                        created_by=self.created_by)

    def accepts_comments_from(self, user):
        if self.public:
            return True
        else:
            return self.active_members.filter(id=user.id).exists()

    def add_comment(self, author=None, message=None):
        if not self.accepts_comments_from(author):
            return None

        return self.comments.create(author=author,
                                    message=message)


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



def combined_membership_count_for_creator(account_id):
    val = Group.objects.filter(created_by=account_id).aggregate(Count('memberships'))['memberships__count']
    val = val if not None else 0

    # Need to subtract all the places where a user has joined their own group
    own_groups = Membership.objects.filter(group__created_by=account_id,
                                           account=account_id).aggregate(Count('id'))['id__count']
    own_groups = own_groups if not None else 0
    return val - own_groups


import groups.hooks
