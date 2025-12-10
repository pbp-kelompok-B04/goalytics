from django.views.decorators.csrf import csrf_exempt
from django.urls import path
from . import views


app_name = "transfer_rumour"

urlpatterns = [
    path("json/", views.rumour_list_json, name="json_list"),
    path("json/<slug:slug>/", views.rumour_detail_json, name="json_detail"),
    path("", views.rumour_list, name="list"),
    path("create/", views.rumour_create, name="create"),
    path("<slug:slug>/edit/", views.rumour_update, name="edit"),
    path("<slug:slug>/delete/", views.rumour_delete, name="delete"),
    path("create-flutter/", (views.create_rumour_flutter), name="create_flutter",),
    path("<slug:slug>/update-flutter/", views.update_rumour_flutter, name="update_flutter"),
    path("<slug:slug>/delete-flutter/", views.delete_rumour_flutter, name="delete_flutter"),
    path("<slug:slug>/", views.rumour_detail, name="detail"),

]
