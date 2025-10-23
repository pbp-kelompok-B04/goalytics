from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from PlayerClub_Data.models import Player
from .models import FavoritePlayer
from django.http import JsonResponse

# Create your views here.
@login_required
def favorite_list(request):
    favorites = FavoritePlayer.objects.filter(user=request.user)
    return render(request, 'favorite_list.html', {'favorites': favorites})

@login_required
def add_favorite(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    FavoritePlayer.objects.get_or_create(user=request.user, player=player)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('favorite_player:favorite_list')


@login_required
def remove_favorite(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    FavoritePlayer.objects.filter(user=request.user, player=player).delete()
    return redirect('favorite_player:favorite_list')