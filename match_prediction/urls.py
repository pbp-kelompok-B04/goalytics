from django.urls import path
from . import views

app_name = 'match_prediction'

urlpatterns = [
    # --- MATCH routes ---
    path('', views.MatchListView.as_view(), name='match_list'),  # list all matches
    path('match/<int:pk>/', views.MatchDetailView.as_view(), name='match_detail'),  # view match + predictions
    path('match/add/', views.MatchCreateView.as_view(), name='match_create'),  # ✅ only ONE create route
    path('match/<int:pk>/edit/', views.MatchUpdateView.as_view(), name='match_edit'),
    path('match/<int:pk>/delete/', views.MatchDeleteView.as_view(), name='match_delete'),

    # --- PREDICTION routes ---
    path('match/<int:match_id>/predict/', views.add_prediction, name='add_prediction'),
    path('prediction/<int:pk>/edit/', views.edit_prediction, name='edit_prediction'),
    path('prediction/<int:pk>/delete/', views.delete_prediction, name='delete_prediction'),

    # --- AJAX routes ---
    path('ajax/match/<int:match_id>/predict/', views.ajax_add_prediction, name='ajax_add_prediction'),
    path('ajax/prediction/<int:prediction_id>/upvote/', views.ajax_toggle_upvote, name='ajax_toggle_upvote'),

    # --- UPVOTE (non-AJAX fallback) ---
    path('prediction/<int:prediction_id>/upvote/', views.toggle_upvote, name='toggle_upvote'),

    path('prediction/<int:prediction_id>/upvote/', views.ajax_toggle_upvote, name='ajax_toggle_upvote'),
]
