from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0021_overall_alltime_duelist_notification_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="hero_gold_medals",
            field=models.PositiveIntegerField(
                default=0,
                help_text=(
                    "Permanent count of weekly #1 finishes on this player's Hero "
                    "leaderboard. Never decreased by weekly vote resets."
                ),
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="villain_gold_medals",
            field=models.PositiveIntegerField(
                default=0,
                help_text=(
                    "Permanent count of weekly #1 finishes on this player's Villain "
                    "leaderboard. Never decreased by weekly vote resets."
                ),
            ),
        ),
    ]
