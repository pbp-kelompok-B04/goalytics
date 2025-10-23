from django.urls import path
from . import views

urlpatterns = [
    path('comparison/', views.comparison_view, name='comparison'),
    path('api/player-search/', views.player_search_api, name='player_search_api'),
    path('api/compare-players/', views.compare_players_api, name='compare_players_api'),
    path('players/', views.create_player, name='create_player'),  # Tanpa /api/
    path('players/<int:player_id>/', views.delete_player, name='delete_player'),
]