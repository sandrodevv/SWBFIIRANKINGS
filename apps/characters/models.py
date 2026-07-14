from django.db import models


class Character(models.Model):
    SIDE_HERO = "hero"
    SIDE_VILLAIN = "villain"
    SIDE_CHOICES = [
        (SIDE_HERO, "Hero"),
        (SIDE_VILLAIN, "Villain"),
    ]

    COMBAT_SABER = "saber"
    COMBAT_BLASTER = "blaster"
    COMBAT_BALL = "ball"
    COMBAT_CHOICES = [
        (COMBAT_SABER, "Saber"),
        (COMBAT_BLASTER, "Blaster"),
        (COMBAT_BALL, "Ball"),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    combat_type = models.CharField(
        max_length=10,
        choices=COMBAT_CHOICES,
        default=COMBAT_BLASTER,
        help_text="Saber, blaster, or ball hero archetype.",
    )
    image = models.ImageField(upload_to="characters/", blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def saber_queryset(cls):
        return cls.objects.filter(combat_type=cls.COMBAT_SABER).order_by("side", "name")
