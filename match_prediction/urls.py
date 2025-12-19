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

    # URLS UNTUK FLUTTER (API)
    path('json/', views.show_json, name='show_json'),
    path('json/<int:match_id>/predictions/', views.show_predictions_json, name='show_predictions_json'),
    path('create-flutter/<int:match_id>/', views.create_prediction_flutter, name='create_prediction_flutter'),
    path('json/<int:match_id>/my-prediction/', views.get_user_prediction_json, name='get_user_prediction_json'),
    path('delete-flutter/<int:match_id>/', views.delete_prediction_flutter, name='delete_prediction_flutter'),
    path('get-role/', views.get_user_role, name='get_user_role'),
    path('get-clubs/', views.get_clubs_json, name='get_clubs_json'),
    path('create-match-flutter/', views.create_match_flutter, name='create_match_flutter'),
    path('edit-match-flutter/<int:match_id>/', views.edit_match_flutter, name='edit_match_flutter'),
    path('delete-match-flutter/<int:match_id>/', views.delete_match_flutter, name='delete_match_flutter'),
]