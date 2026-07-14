from django.conf import settings
from django.db import models


class ModeratorLoginLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="moderator_login_logs",
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=512, blank=True)
    logged_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_in_at"]
        verbose_name = "Moderator login log"
        verbose_name_plural = "Moderator login logs"

    def __str__(self):
        return f"{self.user.username} from {self.ip_address} at {self.logged_in_at}"
