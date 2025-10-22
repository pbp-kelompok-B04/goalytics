from django.shortcuts import render
from PlayerClub_Data.models import Player

from django.db.models import Q

def comparison_view(request):
    player1 = player2 = None
    suggestions1 = []
    suggestions2 = []
    query_submitted = False

    if request.method == 'GET':
        name1 = request.GET.get('player1')
        name2 = request.GET.get('player2')

        if name1 and name2:
            query_submitted = True
            
            # Cari player1 dengan suggestions
            players1 = Player.objects.filter(name__icontains=name1)
            suggestions1 = list(players1[:5])  # Ambil 5 suggestions pertama
            player1 = players1.first()  # Ambil yang pertama sebagai hasil utama

            # Cari player2 dengan suggestions
            players2 = Player.objects.filter(name__icontains=name2)
            suggestions2 = list(players2[:5])
            player2 = players2.first()

    # Hitung max values untuk progress bars jika kedua player ditemukan
    max_goals = max_assists = max_yellow_cards = max_red_cards = max_wins = 1
    
    if player1 and player2:
        max_goals = max(player1.total_goals or 0, player2.total_goals or 0) or 1
        max_assists = max(player1.total_assists or 0, player2.total_assists or 0) or 1
        max_yellow_cards = max(player1.yellow_cards or 0, player2.yellow_cards or 0) or 1
        max_red_cards = max(player1.red_cards or 0, player2.red_cards or 0) or 1
        max_wins = max(player1.total_win or 0, player2.total_win or 0) or 1

    return render(request, 'comparison/comparison.html', {
        'player1': player1,
        'player2': player2,
        'suggestions1': suggestions1,
        'suggestions2': suggestions2,
        'query_submitted': query_submitted,
        'max_goals': max_goals,
        'max_assists': max_assists,
        'max_yellow_cards': max_yellow_cards,
        'max_red_cards': max_red_cards,
        'max_wins': max_wins,
    })
