# Generated by Django 1.11.6 on 2017-12-08 04:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("awards", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="award",
            name="award_type",
            field=models.CharField(
                choices=[
                    ("STUDENT", "Student"),
                    ("MASTER", "Master"),
                    ("SHARER", "Sharer"),
                    ("TREND_SETTER", "Trend setter"),
                    ("ACE", "Ace"),
                    ("RECRUITER", "Recruiter"),
                    ("HACKER", "Hacker"),
                    ("WEEKLY_CHAMPION", "Weekly champion"),
                    ("REIGNING_WEEKLY_CHAMPION", "Reigning weekly champion"),
                    ("ADDICT", "Addict"),
                    ("ORGANIZER", "Organizer"),
                    ("CONSISTENT_LEARNER", "Consistent learner"),
                ],
                max_length=40,
            ),
        ),
    ]
