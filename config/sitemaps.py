from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.characters.models import Character
from apps.rankings.models import Player


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0
    protocol = "https"

    def items(self):
        return ["home", "pfp", "pfp-how", "duelists"]

    def location(self, item):
        return reverse(item)


class CharacterSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Character.objects.order_by("name")

    def location(self, obj):
        return reverse("character-detail", kwargs={"slug": obj.slug})


class PlayerSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Player.objects.exclude(slug="").order_by("nickname")

    def location(self, obj):
        return reverse("player-detail", kwargs={"slug": obj.slug})


sitemaps = {
    "static": StaticViewSitemap,
    "characters": CharacterSitemap,
    "players": PlayerSitemap,
}
