from django.urls import path
from authentication.views import login, register, get_user_info

app_name = 'authentication'

urlpatterns = [
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('user-info/', get_user_info, name='user_info'),
]