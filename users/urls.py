from django.urls import path
from users.views import login_user, register_user, logout_user
from users import views

app_name = 'users'

urlpatterns = [
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/<str:username>/', views.view_profile, name='profile'),
    path('search/', views.search_users, name='search_users'),
    path('search.json', views.search_users_api, name='search_users_api'),
]
