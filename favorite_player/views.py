from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from PlayerClub_Data.models import Player

from .models import FavoritePlayer

# Create your views here.
@login_required
def favorite_list(request):
    query = (request.GET.get('q') or '').strip()

    favorites = (
        FavoritePlayer.objects
        .filter(user=request.user)
        .select_related('player', 'player__club')
        .order_by('player__name')
    )

    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        players_qs = players_qs.filter(name__icontains=query)

    total_players = players_qs.count()
    players_qs = players_qs[:50]
    players = list(players_qs)
    limited = total_players > len(players)

    favorite_ids = set(favorites.values_list('player_id', flat=True))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'partials/player_results.html',
            {
                'players': players,
                'favorite_ids': favorite_ids,
                'limited': limited,
            },
            request=request,
        )
        return JsonResponse({
            'html': html,
            'count': len(players),
            'limited': limited,
        })

    context = {
        'favorites': favorites,
        'players': players,
        'favorite_ids': favorite_ids,
        'search_query': query,
        'players_limited': limited,
    }
    return render(request, 'favorite_list.html', context)

@login_required
def add_favorite(request, player_id):
    player = get_object_or_404(Player, id=player_id)

    if request.method == 'POST':
        FavoritePlayer.objects.get_or_create(user=request.user, player=player)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('favorite_player:favorite_list')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False}, status=405)

    return redirect('favorite_player:favorite_list')


@login_required
def remove_favorite(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    if request.method == 'POST':
        FavoritePlayer.objects.filter(user=request.user, player=player).delete()
    return redirect('favorite_player:favorite_list')
