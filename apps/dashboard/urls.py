from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="dashboard-login"),
    path("logout/", views.logout_view, name="dashboard-logout"),
    path("", views.home_view, name="dashboard-home"),
]
