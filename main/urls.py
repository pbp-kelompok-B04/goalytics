from django.urls import path
from main.views import home, dashboard

app_name = 'main'

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
]
