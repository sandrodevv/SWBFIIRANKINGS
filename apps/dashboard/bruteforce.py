from django.conf import settings
from django.core.cache import cache


def _failures_key(ip):
    return f"dashboard:login:fail:{ip}"


def _lock_key(ip):
    return f"dashboard:login:lock:{ip}"


def _lockout_seconds():
    return getattr(settings, "DASHBOARD_LOGIN_LOCKOUT_SECONDS", 900)


def _max_attempts():
    return getattr(settings, "DASHBOARD_LOGIN_MAX_ATTEMPTS", 5)


def is_login_locked(ip):
    if not ip:
        return False
    return cache.get(_lock_key(ip)) is not None


def record_failed_login(ip):
    if not ip:
        return

    lockout = _lockout_seconds()
    failures_key = _failures_key(ip)
    attempts = cache.get(failures_key, 0) + 1
    cache.set(failures_key, attempts, timeout=lockout)

    if attempts >= _max_attempts():
        cache.set(_lock_key(ip), True, timeout=lockout)


def clear_failed_logins(ip):
    if not ip:
        return
    cache.delete(_failures_key(ip))
    cache.delete(_lock_key(ip))


def lockout_minutes():
    return max(1, _lockout_seconds() // 60)
