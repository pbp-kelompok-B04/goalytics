from django.urls import path
from users.views import login_user, register_user, logout_user, view_profile, search_users, search_users_api, toggle_block_user, toggle_flag_user,  profile_me_api, list_users_api, profile_detail_api


app_name = 'users'

urlpatterns = [
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/<str:username>/', view_profile, name='profile'),
    path('block/<str:username>/', toggle_block_user, name='block_user'),
    path('flag/<str:username>/', toggle_flag_user, name='flag_user'),
    path('search/', search_users, name='search_users'),
    path('search.json', search_users_api, name='search_users_api'),
    path('api/me/', profile_me_api, name='profile_me_api'),
    path('api/users/', list_users_api, name='list_users_api'),
    path('api/profile/<str:username>/', profile_detail_api, name='profile_detail_api'),
    path('image-proxy/', image_proxy, name='image_proxy'),
]
