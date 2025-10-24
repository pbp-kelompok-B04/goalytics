from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "favorite_team", "is_blocked", "is_flagged")
    list_filter = ("role", "favorite_league", "preferred_position", "is_blocked", "is_flagged")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user", "favorite_team")
