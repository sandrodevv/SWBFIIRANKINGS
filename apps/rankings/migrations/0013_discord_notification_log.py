from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rankings", "0012_last_week_votes"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiscordNotificationLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("pfp_weekly_ending", "PFP weekly ending rankings"),
                        ],
                        max_length=64,
                    ),
                ),
                (
                    "period_started_at",
                    models.DateTimeField(
                        help_text="WeeklyVotePeriod.started_at this notification belongs to."
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("sent", "Sent"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("entry_count", models.PositiveIntegerField(default=0)),
                ("detail", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Discord notification log",
                "verbose_name_plural": "Discord notification logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="discordnotificationlog",
            constraint=models.UniqueConstraint(
                fields=("notification_type", "period_started_at"),
                name="unique_discord_notification_per_period",
            ),
        ),
    ]
