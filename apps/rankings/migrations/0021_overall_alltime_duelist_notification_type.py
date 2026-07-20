# Generated manually for overall all-time duelist Discord notification type

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0020_alter_discordnotificationlog_notification_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discordnotificationlog",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("pfp_weekly_ending", "PFP weekly ending rankings"),
                    ("eu_duelist_weekly_winners", "EU duelist weekly winners"),
                    ("us_duelist_weekly_winners", "US duelist weekly winners"),
                    ("au_duelist_weekly_winners", "AU duelist weekly winners"),
                    (
                        "overall_alltime_duelist",
                        "Overall all-time duelist leaderboard",
                    ),
                ],
                max_length=64,
            ),
        ),
    ]
