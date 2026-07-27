from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0025_player_name_beskar"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="name_particles",
            field=models.BooleanField(
                default=False,
                help_text="Show the particle-text nickname animation on this player everywhere.",
            ),
        ),
    ]
