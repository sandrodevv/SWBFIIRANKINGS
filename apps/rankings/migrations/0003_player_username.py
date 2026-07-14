import re

from django.db import migrations, models


def populate_usernames(apps, schema_editor):
    Player = apps.get_model("rankings", "Player")
    for player in Player.objects.all():
        base = re.sub(r"[^a-z0-9_]", "", player.nickname.lower())
        if not base:
            base = f"player{player.pk}"
        username = base
        counter = 1
        while Player.objects.filter(username=username).exclude(pk=player.pk).exists():
            username = f"{base}{counter}"
            counter += 1
        player.username = username
        player.save(update_fields=["username"])


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0002_voterecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="username",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.RunPython(populate_usernames, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="player",
            name="username",
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
