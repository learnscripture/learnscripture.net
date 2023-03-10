# Generated by Django 1.11.6 on 2018-03-26 07:14

from datetime import timedelta

from django.db import migrations, models


def forwards(apps, schema_editor):
    # Fix up missing ActionLog.award field
    # We should use apps.get_model but there is a lot of logic from awards that we need.

    from scores.models import ActionLog, ScoreReason, TotalScore

    corrected = 0
    failed = 0
    used_awards = {log.award for log in ActionLog.objects.filter(award__isnull=False)}
    failed = set()
    for log in ActionLog.objects.filter(reason=ScoreReason.EARNED_AWARD, award__isnull=True):
        candidates = log.account.awards.filter(
            created__gt=log.created - timedelta(seconds=10), created__lt=log.created + timedelta(seconds=10)
        )

        candidates2 = [a for a in candidates if a.award_detail.points() == log.points and a not in used_awards]
        if len(candidates2) == 0:
            print(f"Log {log.id}: Couldn't find award")
            failed.add(log)
            continue
        elif len(candidates2) > 1:
            # Pick the one closer in time.
            sorted_candidates = sorted(candidates2, key=lambda c: abs((log.created - c.created).seconds))
            award = sorted_candidates[0]
        else:
            award = candidates2[0]

        log.award = award
        used_awards.add(award)
        log.save()
        corrected += 1

    for log in list(failed):
        # See if we can match up by points alone, now that most of the
        # items should be associated
        candidates = log.account.awards.filter(actionlog__isnull=True)
        candidates2 = [a for a in candidates if a.award_detail.points() == log.points and a not in used_awards]
        if len(candidates2) == 1:
            award = candidates2[0]
            print(f"Found match for ActionLog {log} {log.__dict__}")
            print(f"Award: {award.id} {award.__dict__}")
            log.award = award
            used_awards.add(award)
            log.save()
            corrected += 1
            failed.remove(log)

    print(f"Corrected: {corrected}")
    print(f"Failed: {len(failed)}")

    # We've investigated these ones and it's OK to delete:
    deletable = [261578, 259923]

    deleted = set()
    for log in list(failed):
        if log.id in deletable:
            failed.remove(log)
            deleted.add(log)
            log.delete()

    if len(failed) < 0:
        raise AssertionError("We didn't fix everything!")

    for log in deleted:
        # Check we are left with correct scores
        assert (
            TotalScore.objects.get(account=log.account).points
            == log.account.action_logs.aggregate(models.Sum("points"))["points__sum"]
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("scores", "0009_auto_20180326_0730"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
