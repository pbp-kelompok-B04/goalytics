from django.urls import path
from . import views

urlpatterns = [
    path('api/posts/', views.get_all_post, name='get_all_post'),
    path('api/posts/mypost', views.get_my_posts, name='get_my_post'),
    path('api/posts/<int:post_id>', views.get_post_by_id, name='get_post_by_id'),

    path("api/posts/", views.create_post, name="create_post"),        

    path("api/posts/<int:post_id>/comments/", views.get_post_comment, name="get_post_comment"),     
    path("api/posts/<int:post_id>/comments/", views.create_comment, name="create_comment"),  
   
]