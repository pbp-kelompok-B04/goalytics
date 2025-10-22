from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Player, Club
from .forms import PlayerForm, ClubForm

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
