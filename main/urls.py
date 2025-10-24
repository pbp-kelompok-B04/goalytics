from django.urls import path, include
from main.views import home, dashboard
from django.contrib.auth import views as auth_views

app_name = 'main'

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
]
