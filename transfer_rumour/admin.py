from django.contrib import admin

from .models import TransferRumour


@admin.register(TransferRumour)
class TransferRumourAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "updated_at")
    list_filter = ("created_at", "author")
    search_fields = ("title", "summary", "content", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    actions = None
