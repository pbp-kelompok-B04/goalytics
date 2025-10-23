from django.urls import path
from . import views

urlpatterns = [
    path('', views.forum_home, name='forum_home'),

    path('api/posts/', views.get_all_post, name='get_all_post'),
    path('api/posts/mypost/', views.get_my_posts, name='get_my_post'),
    path('api/posts/<int:post_id>/', views.get_post_by_id, name='get_post_by_id'),
    path("api/posts/create/", views.create_post, name="create_post"),
    path("api/posts/update", views.update_post, name="update_post"),
    path("api/posts/liked", views.like_post, name="like_post"),
    path("api/posts/delete", views.delete_post, name="delete_post"),

    path("api/posts/<int:post_id>/comments/", views.get_post_comment, name="get_post_comment"),
    path("api/posts/<int:post_id>/comments/create/", views.create_comment, name="create_comment"),
    path("api/comments/update", views.update_comment, name="update_comment"),
    path("api/comments/liked", views.like_comment, name="like_comment"),
    path("api/comments/delete", views.delete_comment, name="delete_comment"),

    # RESTful v1 endpoints (added alongside existing routes)
    path('api/v1/posts/', views.posts_collection, name='v1_posts'),
    path('api/v1/posts/<int:post_id>/', views.post_detail, name='v1_post_detail'),
    path('api/v1/posts/<int:post_id>/likes/', views.post_likes, name='v1_post_likes'),
    path('api/v1/posts/<int:post_id>/comments/', views.comments_collection, name='v1_post_comments'),
    path('api/v1/comments/<int:comment_id>/', views.comment_detail, name='v1_comment_detail'),
    path('api/v1/comments/<int:comment_id>/likes/', views.comment_likes, name='v1_comment_likes'),
]
