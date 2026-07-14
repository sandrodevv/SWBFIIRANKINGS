from django.contrib import admin

from .models import ModeratorLoginLog


@admin.register(ModeratorLoginLog)
class ModeratorLoginLogAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "logged_in_at")
    list_filter = ("logged_in_at", "user")
    search_fields = ("user__username", "ip_address")
    readonly_fields = ("user", "ip_address", "user_agent", "logged_in_at")
    ordering = ("-logged_in_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
