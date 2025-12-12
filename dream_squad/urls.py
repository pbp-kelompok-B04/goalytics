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


    # AJAX actions for adding/removing players (POST)
    path('add/<int:squad_id>/<int:player_id>/', views.add_player_to_squad, name='add_to_squad'),
    path('remove/<int:squad_id>/<int:player_id>/', views.remove_player_from_squad, name='remove_from_squad'),
]
