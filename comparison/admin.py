from django.contrib import admin
from .models import SavedComparison

@admin.register(SavedComparison)
class SavedComparisonAdmin(admin.ModelAdmin):

    list_display = ("get_comparison_title", "user", "created_at")
    search_fields = ("player1__name", "player2__name", "user__username", "notes")
    list_filter = ("user", "created_at")
    autocomplete_fields = ("user", "player1", "player2")
    readonly_fields = ("created_at",)

    def get_comparison_title(self, obj):
        return f"{obj.player1.name} vs {obj.player2.name}"
    get_comparison_title.short_description = "Comparison"
