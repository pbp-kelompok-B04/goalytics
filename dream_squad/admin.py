from django.contrib import admin
from .models import DreamSquad, DreamSquadPlayer

@admin.register(DreamSquad)
class DreamSquadAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("created_at",)
    autocomplete_fields = ("user",)

@admin.register(DreamSquadPlayer)
class DreamSquadPlayerAdmin(admin.ModelAdmin):
    list_display = ("squad", "player", "added_at")
    search_fields = ("squad__name", "player__name")
    autocomplete_fields = ("squad", "player")
