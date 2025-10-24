from django.urls import path

from . import views

app_name = "transfer_rumour"

urlpatterns = [
    path("", views.rumour_list, name="list"),
    path("create/", views.rumour_create, name="create"),
    path("<slug:slug>/edit/", views.rumour_update, name="edit"),
    path("<slug:slug>/delete/", views.rumour_delete, name="delete"),
    path("<slug:slug>/", views.rumour_detail, name="detail"),
]
