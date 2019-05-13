## Groups.

# Help text for the 'public' field when creating a Group
groups-public-group-help-text = A public group is visible to everyone, and so is the member list. This can't be undone once selected.

# Help text for the 'open' field when creating a Group
groups-open-group-help-text = Anyone can join an open group. For a closed group, you have to specifically invite people. A group must be public to be open.

# Caption for the 'name' field of groups
groups-name = Name

# Caption for the 'description' field of groups
groups-description = Description

# Caption for the language field (primary language the group uses)
groups-language = Language
                .help-text = The main language used in the group

# Caption for the 'invited users' field of groups
groups-invited-users = Invited users

## Group list page.

# Page title
groups-page-title = Groups

# Show at top of group list page
groups-list-intro-html =
    By joining groups, you can more easily compare your progress to people that
    you know or are associated with. Search for groups below,
    or <a href="{ $create_group_url }">create your own</a>.

# Label next to box for searching for groups
groups-search-label = Search:

# Button for doing the search
groups-search-button = Search

# Error message displayed if user didn't enter any terms to search for
groups-search-enter-search-term = Please enter a search term.

# Sub-title for search results
groups-search-results-subtitle = Search results:

# Error message displayed if user no groups are found that match the search terms
groups-search-no-results = Sorry, no groups found!



# Caption for the sorting options of the group messages
groups-messages-order = Order

# Caption for showing most recent message first
groups-messages-order-most-recent-first = Most recent first

# Caption for showing oldest message first
groups-messages-order-oldest-first = Oldest first

# Caption for the search input box for searching for groups
groups-search = Search

## Individual group page.

# Page title,
# $name is name of group
groups-group-page-title = Group: { $name }

# Notice displayed after being removed from a group (at user's request),
# $name is group name
groups-removed-from-group = Removed you from group { $name }

# Notice displayed after being added to a group (at user's request)
groups-added-to-group = Added you to group { $name }

# Link that will show other groups
groups-other-groups-link = Other groups

# Sub title for section that shows some stats about the group
groups-statistics-subtitle = Group stats


# Shows when a group was created and by whom
groups-group-created-by-and-when-html = Created by { $creator }, on { DATETIME($created_date) }.


## Group 'wall' page (where group messages are displayed):

# Page title
groups-wall-page-title = Group wall: { $name }

# Link to group wall page
groups-wall-page-link = Group wall

## Group leaderboard page (scores page)

# Page title
groups-leaderboard-page-title = Leaderboard: { $name }



## Create/edit group page.

# Page title when editing
groups-edit-page-title = Edit group: { $name }

# Link/button to edit a group being viewed
groups-edit-group-button = Edit this group


# Page title when creating
groups-create-page-title = Create group

# Success message when group details are updated
groups-group-created = Group details saved.

# Sub-title.
groups-edit-details-subtitle = Group details

# Caption for button that saves the group details
groups-edit-save-group-button = Save group

## Group details page.

# Description sub-title
groups-details-description-subtitle = Description

# Comments sub-title
groups-details-comments-subtitle = Recent comments

# Explains the order of the comments
groups-details-comments-order = Most recent comments first.

# Link that takes the user to the page showing all comments
groups-details-comments-see-all = See all comments.

# Sub-title for section with more group information
groups-details-group-info-subtitle = Group info

# Explanation of 'public' groups
groups-details-public-explanation-html = <b>Public</b>: the group and its member list are visible to
        everyone.

# Explanation of 'private' groups
groups-details-private-explanation-html = <b>Private</b>: the group and its member list are visible only to
        members and invited users.

# Explanation of 'open' groups
groups-details-open-explanation-html = <b>Open</b>: anyone may join.

# Explanation of 'closed' groups
groups-details-closed-explanation-html = <b>Closed</b>: only invited users can join.

# Sub-title for section that shows whether user is in group or could join
groups-details-your-status-subtitle = Your status

# Shown when the user is not a member of the group
groups-details-status-not-member = You are not a member of this group.

# Explanation of what happens when you join a group
groups-details-join-explanation-html = By joining this group, you will join the <b>leaderboard</b> for the group, and the
          <b>news stream</b> on your dashboard will be customised to prefer news from
          the people in this group.

# Explanation of what privacy of joining group
groups-details-join-privacy-note = Joining groups is a public action, unless the group is private and remains
          private.


# Shown when the user is a member
groups-details-status-member = You are a member of this group.


# Button to join a group
groups-details-join-button = Join group

# Button to leave a group
groups-details-leave-button = Leave group

# Group members list sub-title
groups-details-members-subtitle = Members

# Shown when there are no members.
groups-details-members-empty = No members in this group

