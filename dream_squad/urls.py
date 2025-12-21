# urls.py
from django.urls import path
from . import views

app_name = 'dream_squad'  # tetap agar template URL reverse tetap valid

urlpatterns = [
    path('', views.squad_list, name='dream_squad'),  # reuse route - tampilkan squads
    path('create/', views.create_squad, name='create_squad'),
    path('<int:squad_id>/', views.squad_detail, name='squad_detail'),  # detail & edit page
    path('<int:squad_id>/edit/', views.edit_squad, name='edit_squad'),
    path('<int:squad_id>/delete/', views.delete_squad, name='delete_squad'),
    path('select/<int:player_id>/', views.select_squad_for_player, name='select_squad_for_player'),
    path('player/<int:player_id>/', views.player_detail, name='player_detail'),
    path('add/<int:squad_id>/<int:player_id>/', views.add_player_to_squad, name='add_to_squad'),
    path('remove/<int:squad_id>/<int:player_id>/', views.remove_player_from_squad, name='remove_from_squad'),

    #API
    path('api/squads/', views.squad_list_api, name='squad_list_api'),
    path('api/<int:squad_id>/', views.squad_detail_api, name='squad_detail_api'),
    path('api/add/<int:squad_id>/<int:player_id>/', views.add_player_to_squad_api, name='add_player_api'),
    path('api/remove/<int:squad_id>/<int:player_id>/', views.remove_player_from_squad_api, name='remove_player_api'),
    path('api/create/', views.create_squad_api, name='create_squad_api'),
    path('api/delete/<int:squad_id>/', views.delete_squad_api, name='delete_squad_api'),
    path('api/edit/<int:squad_id>/', views.edit_squad_api, name='edit_squad_api'),
    path('api/player/<int:player_id>/', views.api_player_detail, name='api_player_detail'),
    path('api/players-modal/', views.get_players_for_modal),
]
