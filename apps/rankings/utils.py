from django.apps import apps
from django.utils.text import slugify


def generate_unique_player_slug(nickname, exclude_pk=None):
    Player = apps.get_model("rankings", "Player")
    base = slugify(nickname) or "player"
    slug = base
    counter = 1
    queryset = Player.objects.filter(slug=slug)
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    while queryset.exists():
        slug = f"{base}-{counter}"
        counter += 1
        queryset = Player.objects.filter(slug=slug)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
    return slug
