from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Player, Club
from .forms import PlayerForm, ClubForm
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'admin'

@login_required
def database_home(request):
    return render(request, 'database_home.html')

@login_required
def player_list(request):
    players = Player.objects.all().select_related('club')
    context = {'players': players, 'is_admin': is_admin(request.user)}
    return render(request, 'player_list.html', context)


@login_required
@user_passes_test(is_admin)
def player_create(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Player added successfully.")
            return redirect('PlayerClub_Data:player_list')
    else:
        form = PlayerForm()
    return render(request, 'player_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, "Player updated successfully.")
            return redirect('PlayerClub_Data:player_list')
    else:
        form = PlayerForm(instance=player)
    return render(request, 'player_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        player.delete()
        messages.success(request, "Player deleted successfully.")
        return redirect('PlayerClub_Data:player_list')
    return render(request, 'player_delete.html', {'player': player})

@login_required
def club_list(request):
    clubs = Club.objects.all()
    context = {'clubs': clubs, 'is_admin': is_admin(request.user)}
    return render(request, 'club_list.html', context)

@login_required
@user_passes_test(is_admin)
def club_create(request):
    if request.method == 'POST':
        form = ClubForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Club added successfully.")
            return redirect('PlayerClub_Data:club_list')
    else:
        form = ClubForm()
    return render(request, 'club_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def club_update(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.method == 'POST':
        form = ClubForm(request.POST, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, "Club updated successfully.")
            return redirect('PlayerClub_Data:club_list')
    else:
        form = ClubForm(instance=club)
    return render(request, 'club_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def club_delete(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.method == 'POST':
        club.delete()
        messages.success(request, "Club deleted successfully.")
        return redirect('PlayerClub_Data:club_list')
    return render(request, 'club_delete.html', {'club': club})

#ajax
@login_required
@require_http_methods(["GET"])
def get_all_player(request):
    players = (
        Player.objects.select_related("club")
        .all()
        .order_by("-goals", "name")
    )
    data = []
    for p in players:
        item = {
            "id": p.id,
            "name": p.name,
            "nation": p.nation,
            "position": p.position,
            "age": p.age,
            "born": p.born,
            "club": p.club.name if p.club else None,
            "goals": p.goals,
            "assists": p.assists,
            "xg": p.xg,
            "npxg": p.npxg,
            "xag": p.xag,
            "progressive_carries": p.Progressive_Carries,
            "progressive_passes": p.Progressive_Passes,
            "progressive_receptions": p.Progressive_Receptions,
            "passes_completed": p.passes_completed,
            "passes_attempted": p.passes_attempted,
            "pass_accuracy": p.pass_accuracy,
            "tackles": p.tackles,
            "tackles_won": p.tackles_won,
            "challenges_won": p.challenges_won,
            "challenges_attempted": p.challenges_attempted,
            "blocks": p.blocks,
            "clearances": p.clearances,
            "saves": p.saves,
            "save_percentage": p.save_percentage,
            "clean_sheets": p.clean_sheets,
            "clean_sheet_percentage": p.clean_sheet_percentage,
        }
        data.append(item)

    return JsonResponse({"data": data})
    