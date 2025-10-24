from django.urls import path
from . import views

app_name = 'match_prediction'

urlpatterns = [
    # --- MATCH routes ---
    path('', views.MatchListView.as_view(), name='match_list'), 
    path('match/<int:pk>/', views.MatchDetailView.as_view(), name='match_detail'), 
    path('match/add/', views.MatchCreateView.as_view(), name='match_create'), 
    path('match/<int:pk>/edit/', views.MatchUpdateView.as_view(), name='match_edit'),
    path('match/<int:pk>/delete/', views.MatchDeleteView.as_view(), name='match_delete'),

    # --- PREDICTION routes ---
    path('match/<int:match_id>/predict/', views.add_prediction, name='add_prediction'),
    path('prediction/<int:pk>/edit/', views.edit_prediction, name='edit_prediction'),
    path('prediction/<int:pk>/delete/', views.delete_prediction, name='delete_prediction'),

    # --- AJAX routes ---
    path('ajax/match/<int:match_id>/predict/', views.ajax_add_prediction, name='ajax_add_prediction'),
    # CRITICAL FIX: This is the ONLY ajax_toggle_upvote entry.
    path('ajax/prediction/<int:prediction_id>/upvote/', views.ajax_toggle_upvote, name='ajax_toggle_upvote'),

    # --- UPVOTE (non-AJAX fallback, renamed for clarity) ---
    path('prediction/<int:prediction_id>/upvote/', views.toggle_upvote, name='toggle_upvote_fallback'),
]