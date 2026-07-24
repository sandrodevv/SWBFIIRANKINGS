from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0022_player_gold_medals"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="youtube_url",
            field=models.URLField(
                blank=True,
                help_text="Public YouTube channel or video link for this player.",
            ),
        ),
    ]
