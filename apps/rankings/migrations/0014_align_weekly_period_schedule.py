from django.db import migrations


def align_weekly_period_to_sunday_schedule(apps, schema_editor):
    """Snap WeeklyVotePeriod.started_at to the current schedule without wiping votes."""
    from apps.rankings.services.weekly_reset import align_period_to_schedule

    align_period_to_schedule(reset_votes=False)


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0013_discord_notification_log"),
    ]

    operations = [
        migrations.RunPython(
            align_weekly_period_to_sunday_schedule,
            migrations.RunPython.noop,
        ),
    ]
