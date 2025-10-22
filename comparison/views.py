from django.shortcuts import render
from PlayerClub_Data.models import Player

def comparison_view(request):
    player1 = player2 = None

    if request.method == 'GET':
        name1 = request.GET.get('player1')
        name2 = request.GET.get('player2')

        if name1 and name2:
            player1 = Player.objects.filter(name__iexact=name1).first()
            player2 = Player.objects.filter(name__iexact=name2).first()

    return render(request, 'comparison/comparison.html', {
        'player1': player1,
        'player2': player2
    })
