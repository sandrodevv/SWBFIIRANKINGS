from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0030_player_name_stroke"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="player",
            name="name_stroke",
        ),
    ]
