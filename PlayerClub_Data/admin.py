from django.contrib import admin

from .models import Club, Player


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "season", "total_goal", "total_assist")
    search_fields = ("name", "league")
    list_filter = ("league", "season")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "club", "goals", "assists")
    search_fields = ("name", "nation", "club__name")
    list_filter = ("position", "club__league")
    autocomplete_fields = ("club",)
