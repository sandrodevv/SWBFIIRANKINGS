from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0029_player_name_crack"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="name_stroke",
            field=models.BooleanField(
                default=False,
                help_text="Show the multi-stroke SVG nickname animation on this player everywhere.",
            ),
        ),
    ]
