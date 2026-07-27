from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0027_player_name_mesh"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="player",
            name="name_mesh",
        ),
    ]
