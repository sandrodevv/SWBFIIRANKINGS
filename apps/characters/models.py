from django.db import models
from django.conf import settings


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

    STATIC_IMAGE_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")

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

    def resolve_static_image_path(self) -> str:
        """
        Return the first matching static character image path.

        Prefers webp, then png, then jpg/jpeg under
        frontend/static/images/characters/{slug}.*
        """
        relative_dir = settings.BASE_DIR / "frontend" / "static" / "images" / "characters"
        for extension in self.STATIC_IMAGE_EXTENSIONS:
            candidate = relative_dir / f"{self.slug}{extension}"
            if candidate.is_file():
                return f"/static/images/characters/{self.slug}{extension}"
        return f"/static/images/characters/{self.slug}.jpg"

    def get_image_url(self, request=None) -> str:
        if self.image:
            url = self.image.url
        else:
            url = self.resolve_static_image_path()
        if request is not None:
            return request.build_absolute_uri(url)
        return url
