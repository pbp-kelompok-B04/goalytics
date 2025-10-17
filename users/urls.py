from django.urls import path
from users.views import login_user, register_user, logout_user, profile_view

app_name = 'users'

urlpatterns = [
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/', profile_view, name='profile'),
]
