Most of this config is deployed by 'fab deploy'

There is some non-automatic config that needs to be deployed, due to the
way we are using hosting:

- crontab file
- reminders@learnscripture.net is set up on WebFaction control pannel to be handled by
  /home/cciw/webapps/learnscripture_django/src/scripts/handle_reminder_bounces.py
