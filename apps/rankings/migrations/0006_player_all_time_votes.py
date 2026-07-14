from django.db import migrations, models
from django.db.models import Sum


def backfill_player_all_time_votes(apps, schema_editor):
    Player = apps.get_model("rankings", "Player")
    CharacterRanking = apps.get_model("rankings", "CharacterRanking")

    for player in Player.objects.all():
        total = (
            CharacterRanking.objects.filter(player_id=player.pk).aggregate(
                total=Sum("all_time_votes")
            )["total"]
            or 0
        )
        player.all_time_votes = total
        player.save(update_fields=["all_time_votes"])


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0005_weekly_reset_all_time_votes"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="all_time_votes",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Total votes received across all characters and weekly periods.",
            ),
        ),
        migrations.RunPython(backfill_player_all_time_votes, migrations.RunPython.noop),
    ]
