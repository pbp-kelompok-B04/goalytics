from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Player, Club
from .forms import PlayerForm, ClubForm
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Count

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
    players = (Player.objects.select_related("club").all())
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


@login_required
@require_http_methods(["POST"])
@user_passes_test(is_admin)
def player_create_api(request):
    form_data = {
        field_name: field_value
        for field_name, field_value in request.POST.items()
        if field_name not in ["csrfmiddlewaretoken", "_method"]
    }
    cleaned_data = {}
    for field_name, field_value in form_data.items():
        cleaned_data[field_name] = field_value or None
    club_id = cleaned_data.get("club")
    club_instance = None
    if club_id:
        try:
            club_instance = Club.objects.get(pk=int(club_id))
        except (Club.DoesNotExist, ValueError):
            return JsonResponse({"error": "Club not found"}, status=404)

    player = Player.objects.create(
        name=cleaned_data.get("name"),
        nation=cleaned_data.get("nation"),
        position=cleaned_data.get("position"),
        age=cleaned_data.get("age") or None,
        born=cleaned_data.get("born") or None,
        club=club_instance,
        goals=cleaned_data.get("goals") or 0,
        assists=cleaned_data.get("assists") or 0,
        xg=cleaned_data.get("xg") or 0,
        npxg=cleaned_data.get("npxg") or 0,
        xag=cleaned_data.get("xag") or 0,
        Progressive_Carries=cleaned_data.get("progressive_carries") or 0,
        Progressive_Passes=cleaned_data.get("progressive_passes") or 0,
        Progressive_Receptions=cleaned_data.get("progressive_receptions") or 0,
        passes_completed=cleaned_data.get("passes_completed") or 0,
        passes_attempted=cleaned_data.get("passes_attempted") or 0,
        pass_accuracy=cleaned_data.get("pass_accuracy") or 0,
        tackles=cleaned_data.get("tackles") or 0,
        tackles_won=cleaned_data.get("tackles_won") or 0,
        challenges_won=cleaned_data.get("challenges_won") or 0,
        challenges_attempted=cleaned_data.get("challenges_attempted") or 0,
        blocks=cleaned_data.get("blocks") or 0,
        clearances=cleaned_data.get("clearances") or 0,
        saves=cleaned_data.get("saves") or 0,
        save_percentage=cleaned_data.get("save_percentage") or 0,
        clean_sheets=cleaned_data.get("clean_sheets") or 0,
        clean_sheet_percentage=cleaned_data.get("clean_sheet_percentage") or 0,
    )

    return JsonResponse({"message": "Player created successfully"}, status=201)


@login_required
@require_http_methods(["GET"])
def get_all_club(request):
    clubs = Club.objects.all()
    data = []
    for c in clubs:
        item = {
            "id": c.id,
            "name": c.name,
            "league": c.league,
            "season": c.season,
            "total_goal": c.total_goal,
            "total_assist": c.total_assist,
            "expected_xg": c.expected_xg,
            "expected_xag": c.expected_xag,
        }
        data.append(item)
    return JsonResponse({"data": data})

@login_required
@require_http_methods(["POST"])
@user_passes_test(is_admin)
def club_create_api(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "'name' is required"}, status=400)
    if Club.objects.filter(name__iexact=name).exists():
        return JsonResponse({"error": "Club with this name already exists"}, status=400)
    def to_int(val, default=0):
        if val is None or val == "":
            return default
        try:
            return int(val)
        except ValueError:
            return default
    def to_float(val, default=0.0):
        if val is None or val == "":
            return default
        try:
            return float(val)
        except ValueError:
            return default
    club = Club.objects.create(
        league=(request.POST.get("league") or None) or Club._meta.get_field("league").default,
        season=(request.POST.get("season") or None) or Club._meta.get_field("season").default,
        name=name,
        total_goal=to_int(request.POST.get("total_goal"), 0),
        total_assist=to_int(request.POST.get("total_assist"), 0),
        expected_xg=to_float(request.POST.get("expected_xg"), 0.0),
        expected_xag=to_float(request.POST.get("expected_xag"), 0.0),
    )
    data = {
        "id": club.id,
        "name": club.name,
        "league": club.league,
        "season": club.season,
        "total_goal": club.total_goal,
        "total_assist": club.total_assist,
        "expected_xg": club.expected_xg,
        "expected_xag": club.expected_xag,
    }
    return JsonResponse({"message": "Club created successfully", "data": data}, status=201)
