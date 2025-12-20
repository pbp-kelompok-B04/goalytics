from django.contrib import admin
from django.db.models import Count
from PlayerClub_Data.models import Player  # Ambil model punya teman
from .models import DreamSquad, DreamSquadPlayer

# --- BAGIAN MODERASI & STATISTIK ---

try:
    # Kita 'copot' pendaftaran dari PlayerClub_Data agar bisa kita ganti
    admin.site.unregister(Player)
except admin.sites.NotRegistered:
    pass

@admin.register(Player)
class PlayerAnalyticsAdmin(admin.ModelAdmin):
    # Kita gabungkan: Tampilan teman Anda + Statistik Anda
    list_display = ("name", "position", "club", "usage_count", "goals", "assists")
    search_fields = ("name", "nation", "club__name")
    list_filter = ("position", "club__league")
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Menghitung statistik penggunaan pemain di Dream Squad
        return queryset.annotate(_usage_count=Count('in_dream_squads'))

    def usage_count(self, obj):
        return obj._usage_count
    
    usage_count.admin_order_field = '_usage_count'
    usage_count.short_description = "Times Used (Meta)"

# --- BAGIAN MODEL ANDA SENDIRI ---

@admin.register(DreamSquad)
class DreamSquadAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("created_at",)

@admin.register(DreamSquadPlayer)
class DreamSquadPlayerAdmin(admin.ModelAdmin):
    list_display = ("squad", "player", "added_at")