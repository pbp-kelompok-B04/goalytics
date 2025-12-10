from django.urls import path
from . import views


urlpatterns = [
    path('comparison/', views.comparison_view, name='comparison'),
    path('api/player-search/', views.player_search_api, name='player_search_api'),
    path('api/compare-players/', views.compare_players_api, name='compare_players_api'),
    path('players/', views.create_player, name='create_player'), 
    path('players/<int:player_id>/', views.delete_player, name='delete_player'),
    path('api/save-comparison/', views.save_comparison, name='save_comparison'),
    path('comparison-history/', views.comparison_history, name='comparison_history'),
    path('api/saved-comparisons/', views.get_saved_comparisons, name='get_saved_comparisons'),
    path('api/saved-comparisons/<int:comparison_id>/delete/', views.delete_saved_comparison, name='delete_saved_comparison'),
    path('api/players/<int:player_id>/', views.get_player_by_id, name='get_player_by_id'),
    path('api/saved-comparisons/<int:comparison_id>/', views.get_comparison_detail),
    path('api/compare-players-flutter/', views.compare_players_flutter),
    path('api/save-comparison-flutter/', views.save_comparison_flutter),
    path('api/saved-comparisons-flutter/', views.get_saved_comparisons_flutter),
    path('api/saved-comparisons-flutter/<int:comparison_id>/', views.get_comparison_detail),
    path('api/saved-comparisons-flutter/<int:comparison_id>/delete/', views.delete_comparison_flutter, name='delete_comparison_flutter'),
]