from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0011_duelist_link_player"),
    ]

    operations = [
        migrations.AddField(
            model_name="characterranking",
            name="last_week_votes",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Vote count from the previous weekly period (overwritten each reset).",
            ),
        ),
        migrations.AddField(
            model_name="duelist",
            name="last_week_votes",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Vote count from the previous weekly period (overwritten each reset).",
            ),
        ),
    ]
