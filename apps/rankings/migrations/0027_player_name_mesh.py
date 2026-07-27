from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0026_player_name_particles"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="name_mesh",
            field=models.BooleanField(
                default=False,
                help_text="Show the connected mesh particle nickname animation on this player everywhere.",
            ),
        ),
    ]
