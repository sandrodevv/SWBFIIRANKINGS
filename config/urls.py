from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView

from config.sitemaps import sitemap_xml


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /api/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("sitemap.xml", sitemap_xml, name="sitemap"),
    path("robots.txt", robots_txt, name="robots-txt"),
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("pfp/", TemplateView.as_view(template_name="pfp.html"), name="pfp"),
    path(
        "pfp/how-it-works/",
        TemplateView.as_view(template_name="pfp_how.html"),
        name="pfp-how",
    ),
    path(
        "duelists/",
        TemplateView.as_view(template_name="duelists.html"),
        name="duelists",
    ),
    path(
        "characters/<slug:slug>/",
        TemplateView.as_view(template_name="character.html"),
        name="character-detail",
    ),
    path(
        "players/<slug:slug>/",
        TemplateView.as_view(template_name="player.html"),
        name="player-detail",
    ),
]

# Serve uploaded media in all environments (needed on Railway without object storage).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
