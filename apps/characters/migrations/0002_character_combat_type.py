from django.db import migrations, models


SABER_SLUGS = {
    "anakin-skywalker",
    "luke-skywalker",
    "obi-wan-kenobi",
    "rey",
    "yoda",
    "count-dooku",
    "darth-maul",
    "darth-vader",
    "kylo-ren",
    "general-grievous",
}

BALL_SLUGS = {
    "bb-8",
    "bb-9e",
}


def set_combat_types(apps, schema_editor):
    Character = apps.get_model("characters", "Character")
    for character in Character.objects.all():
        if character.slug in SABER_SLUGS:
            combat_type = "saber"
        elif character.slug in BALL_SLUGS:
            combat_type = "ball"
        else:
            combat_type = "blaster"
        if character.combat_type != combat_type:
            character.combat_type = combat_type
            character.save(update_fields=["combat_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("characters", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="character",
            name="combat_type",
            field=models.CharField(
                choices=[
                    ("saber", "Saber"),
                    ("blaster", "Blaster"),
                    ("ball", "Ball"),
                ],
                default="blaster",
                help_text="Saber, blaster, or ball hero archetype.",
                max_length=10,
            ),
        ),
        migrations.RunPython(set_combat_types, migrations.RunPython.noop),
    ]
