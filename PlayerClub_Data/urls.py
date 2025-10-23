from django.urls import path
from PlayerClub_Data.views import (
    player_list,
    player_create,
    player_update,
    player_delete,
    club_list,
    club_create,
    club_update,
    club_delete,
    database_home,
    get_all_player,
    get_all_club,
)

app_name = 'PlayerClub_Data'

urlpatterns = [
    path('database/', database_home, name='database_home'),
    path('players/', player_list, name='player_list'),
    path('api/players/', get_all_player, name='get_all_player'),
    path('api/clubs/', get_all_club, name='get_all_club'),
    path('players/add/', player_create, name='player_create'),
    path('players/<int:pk>/edit/', player_update, name='player_update'),
    path('players/<int:pk>/delete/', player_delete, name='player_delete'),
    path('clubs/', club_list, name='club_list'),
    path('clubs/add/', club_create, name='club_create'),
    path('clubs/<int:pk>/edit/', club_update, name='club_update'),
    path('clubs/<int:pk>/delete/', club_delete, name='club_delete'),
]
