from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0003_player_username"),
    ]

    operations = [
        migrations.AlterField(
            model_name="player",
            name="username",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
