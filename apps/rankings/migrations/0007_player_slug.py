from django.db import migrations, models
from django.utils.text import slugify


def backfill_player_slugs(apps, schema_editor):
    Player = apps.get_model("rankings", "Player")
    used_slugs = set()

    for player in Player.objects.all().order_by("id"):
        base = slugify(player.nickname) or f"player-{player.pk}"
        slug = base
        counter = 1
        while slug in used_slugs:
            slug = f"{base}-{counter}"
            counter += 1
        used_slugs.add(slug)
        player.slug = slug
        player.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0006_player_all_time_votes"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="slug",
            field=models.SlugField(blank=True, max_length=60, null=True),
        ),
        migrations.RunPython(backfill_player_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="player",
            name="slug",
            field=models.SlugField(max_length=60, unique=True),
        ),
    ]
