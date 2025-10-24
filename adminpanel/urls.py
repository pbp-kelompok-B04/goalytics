from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/<int:user_id>/role/", views.update_user_role, name="update_user_role"),
    path("clubs/add/", views.club_create, name="club_create"),
    path("clubs/<int:pk>/edit/", views.club_update, name="club_update"),
    path("clubs/<int:pk>/delete/", views.club_delete, name="club_delete"),
    path("players/add/", views.player_create, name="player_create"),
    path("players/<int:pk>/edit/", views.player_update, name="player_update"),
    path("players/<int:pk>/delete/", views.player_delete, name="player_delete"),
]
