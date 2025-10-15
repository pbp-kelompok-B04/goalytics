from django.urls import path
from . import views

app_name = "goalytics_app"

urlpatterns = [
    # pages (render HTML)
    path("", views.me_page, name="profile.me"),
    path("profile/edit/", views.edit_page, name="profile.edit"),
    path("auth/login/", views.login_page, name="auth.login"),
    path("auth/register/", views.register_page, name="auth.register"),

    # AJAX (JSON)
    path("api/auth/register/", views.api_register, name="api.auth.register"),
    path("api/auth/login/", views.api_login, name="api.auth.login"),
    path("api/auth/logout/", views.api_logout, name="api.auth.logout"),
    path("api/profile/me/", views.api_profile_me, name="api.profile.me"),
    path("api/profile/update/", views.api_profile_update, name="api.profile.update"),
]
