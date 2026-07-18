from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.urls import reverse

from apps.characters.models import Character
from apps.rankings.models import Player


def _abs_url(request, path: str) -> str:
    return request.build_absolute_uri(path)


def sitemap_xml(request):
    """Single flat sitemap for Google Search Console."""
    urls = [
        (_abs_url(request, reverse("home")), "1.0", "daily"),
        (_abs_url(request, reverse("pfp")), "0.9", "daily"),
        (_abs_url(request, reverse("pfp-how")), "0.7", "monthly"),
        (_abs_url(request, reverse("duelists")), "0.9", "daily"),
    ]

    for character in Character.objects.order_by("name").only("slug"):
        urls.append(
            (
                _abs_url(
                    request,
                    reverse("character-detail", kwargs={"slug": character.slug}),
                ),
                "0.9",
                "daily",
            )
        )

    for player in Player.objects.exclude(slug="").order_by("nickname").only("slug"):
        urls.append(
            (
                _abs_url(
                    request,
                    reverse("player-detail", kwargs={"slug": player.slug}),
                ),
                "0.8",
                "daily",
            )
        )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, priority, changefreq in urls:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(loc)}</loc>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return HttpResponse("\n".join(lines) + "\n", content_type="application/xml")
