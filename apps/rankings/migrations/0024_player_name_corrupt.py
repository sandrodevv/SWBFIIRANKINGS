from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0023_player_youtube_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="name_corrupt",
            field=models.BooleanField(
                default=False,
                help_text="Show the corrupt fade/glitch nickname animation on this player everywhere.",
            ),
        ),
    ]
