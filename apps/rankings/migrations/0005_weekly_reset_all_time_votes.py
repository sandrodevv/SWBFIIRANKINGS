from django.db import migrations, models
from django.utils import timezone


def copy_votes_to_all_time(apps, schema_editor):
    CharacterRanking = apps.get_model("rankings", "CharacterRanking")
    for ranking in CharacterRanking.objects.all():
        ranking.all_time_votes = ranking.votes
        ranking.save(update_fields=["all_time_votes"])


def create_initial_period(apps, schema_editor):
    WeeklyVotePeriod = apps.get_model("rankings", "WeeklyVotePeriod")
    WeeklyVotePeriod.objects.get_or_create(
        pk=1,
        defaults={"started_at": timezone.now()},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0004_alter_player_username_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="characterranking",
            name="all_time_votes",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Total votes received across all weekly periods.",
            ),
        ),
        migrations.CreateModel(
            name="WeeklyVotePeriod",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "started_at",
                    models.DateTimeField(
                        help_text="When the current weekly voting period began.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Weekly vote period",
                "verbose_name_plural": "Weekly vote period",
            },
        ),
        migrations.RunPython(copy_votes_to_all_time, migrations.RunPython.noop),
        migrations.RunPython(create_initial_period, migrations.RunPython.noop),
    ]
