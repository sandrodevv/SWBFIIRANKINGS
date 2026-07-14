from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0007_player_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="player",
            name="username",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
