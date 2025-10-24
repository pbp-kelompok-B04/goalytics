from django.contrib import admin

from .models import FavoritePlayer


@admin.register(FavoritePlayer)
class FavoritePlayerAdmin(admin.ModelAdmin):
    list_display = ("user", "player", "added_at")
    search_fields = ("user__username", "player__name")
    list_filter = ("added_at",)
    autocomplete_fields = ("user", "player")
