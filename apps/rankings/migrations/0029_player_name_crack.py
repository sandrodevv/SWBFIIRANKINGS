from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0028_remove_player_name_mesh"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="name_crack",
            field=models.BooleanField(
                default=False,
                help_text="Show the crack/shake nickname animation on this player everywhere.",
            ),
        ),
    ]
