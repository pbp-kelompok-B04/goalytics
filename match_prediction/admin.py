# match_prediction/admin.py
from django.contrib import admin
from .models import Match, Prediction, PredictionUpvote

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'match_datetime', 'venue', 'is_active', 'created_by', 'created_at')
    search_fields = ('home_club__name', 'away_club__name', 'venue')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    list_filter = ('is_active',)

    # Make admin read-only (no add/change/delete). Allow viewing list/detail.
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        # allow viewing object detail page but not saving changes
        if request.method in ('GET', 'HEAD'):
            return True
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'user', 'predicted_home_score', 'predicted_away_score', 'is_deleted', 'created_at')
    search_fields = ('user__username', 'match__home_club__name', 'match__away_club__name')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('is_deleted',)

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        if request.method in ('GET', 'HEAD'):
            return True
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(PredictionUpvote)
class PredictionUpvoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'prediction', 'user', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        # read-only
        if request.method in ('GET', 'HEAD'):
            return True
        return False
    def has_delete_permission(self, request, obj=None):
        return False
