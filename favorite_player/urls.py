from django.urls import path
from . import views

app_name = 'favorite_player'

urlpatterns = [
    path('', views.favorite_list, name='favorite_list'),
    path('add/<int:player_id>/', views.add_favorite, name='add_favorite'),
    path('remove/<int:player_id>/', views.remove_favorite, name='remove_favorite'),
]
