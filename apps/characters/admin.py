from django.contrib import admin

from apps.characters.models import Character


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "side", "combat_type")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
    list_filter = ("side", "combat_type")
