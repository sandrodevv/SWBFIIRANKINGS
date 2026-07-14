from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0008_alter_player_username_non_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="characterranking",
            name="pfp_score",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="characterranking",
            name="pfp_percentile_score",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="characterranking",
            name="pfp_vote_score",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="characterranking",
            name="pfp_competition_score",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="characterranking",
            name="pfp_champion_bonus",
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name="characterranking",
            name="pfp_character_rank",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="characterranking",
            name="pfp_global_rank",
            field=models.PositiveIntegerField(default=0, db_index=True),
        ),
    ]
