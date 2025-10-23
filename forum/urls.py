from django.urls import path
from . import views

urlpatterns = [
    path('', views.forum_home, name='forum_home'),
    path('posts/<int:post_id>/', views.forum_post_detail, name='forum_post_detail'),

    path('api/posts/', views.get_all_post, name='get_all_post'),
    path('api/posts/mypost/', views.get_my_posts, name='get_my_posts'),
    path('api/posts/create/', views.create_post, name='create_post'),
    path('api/posts/<int:post_id>/', views.get_post_by_id, name='get_post_by_id'),
    path('api/posts/<int:post_id>/update/', views.update_post, name='update_post'),
    path('api/posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('api/posts/<int:post_id>/likes/', views.like_post, name='like_post'),

    path('api/posts/<int:post_id>/comments/', views.get_post_comment, name='get_post_comment'),
    path('api/posts/<int:post_id>/comments/create/', views.create_comment, name='create_comment'),
    path('api/comments/<int:comment_id>/update/', views.update_comment, name='update_comment'),
    path('api/comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('api/comments/<int:comment_id>/likes/', views.like_comment, name='like_comment'),
]
