import django.db.models.deletion
from django.db import migrations, models


def clear_orphan_duelists(apps, schema_editor):
    DuelistVoteRecord = apps.get_model("rankings", "DuelistVoteRecord")
    Duelist = apps.get_model("rankings", "Duelist")
    DuelistVoteRecord.objects.all().delete()
    Duelist.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0010_duelist_rankings"),
    ]

    operations = [
        migrations.RunPython(clear_orphan_duelists, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="duelist",
            name="nickname",
        ),
        migrations.RemoveField(
            model_name="duelist",
            name="slug",
        ),
        migrations.RemoveField(
            model_name="duelist",
            name="username",
        ),
        migrations.AddField(
            model_name="duelist",
            name="player",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="duelist",
                to="rankings.player",
            ),
        ),
    ]
