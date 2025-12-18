# views.py
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from PlayerClub_Data.models import Player

from .models import DreamSquad, DreamSquadPlayer
from .forms import DreamSquadForm

# business constraints:
MAX_PLAYERS = 22
REQUIRED_POS = {'GK', 'DF', 'MF', 'FW'}

def squad_has_required_positions(player_qs):
    """Return True if at least one player for each required position exists."""
    positions_present = {p.position for p in player_qs if p.position}
    return REQUIRED_POS.issubset(positions_present)

@login_required
def squad_list(request):
    """Show list of user's squads + player search (UI same as favorite_list)."""
    query = (request.GET.get('q') or '').strip()

    # Prefetch data player melalui model perantara untuk akses yang efisien
    squads = DreamSquad.objects.filter(user=request.user).prefetch_related('players__player')

    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        players_qs = players_qs.filter(name__icontains=query)

    total_players_search_count = players_qs.count()
    players_qs = players_qs[:50]
    players_discovery = list(players_qs)
    limited = total_players_search_count > len(players_discovery)

    # if AJAX (search), render partial player results
    favorite_ids = set()  # Tetap kosong karena tidak ada squad aktif yang dipilih secara default
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'partials/player_results.html',
            {
                'players': players_discovery,
                'favorite_ids': favorite_ids,
                'limited': limited,
                # frontend akan memutuskan squad mana yang akan ditambahkan
            },
            request=request,
        )
        return JsonResponse({
            'html': html,
            'count': len(players_discovery),
            'limited': limited,
        })

    # --- PERHITUNGAN STATS GLOBAL BARU ---
    squad_count = squads.count()
    total_players_in_squads = 0
    total_age = 0
    
    # 1. Iterasi melalui semua squad untuk mengumpulkan total pemain dan total usia
    for sq in squads:
        # sq.players.all() sudah di-prefetch, jadi ini efisien
        for dsp in sq.players.all():
            total_players_in_squads += 1
            
            # Kumpulkan usia
            age = getattr(dsp.player, 'age', None)
            # Pastikan age adalah angka valid sebelum dijumlahkan
            if isinstance(age, (int, float)) and age > 0:
                total_age += age
    
    # 2. Hitung Rata-rata Usia Global
    global_avg_age = round(total_age / total_players_in_squads, 1) if total_players_in_squads > 0 else 0
    # --- END STATS GLOBAL BARU ---

    context = {
        'squads': squads,
        'players': players_discovery,
        'search_query': query,
        'players_limited': limited,
        
        # Menggunakan metrik baru yang disarankan untuk tampilan ringkasan
        'squad_stats': {
            'count': squad_count,                       # 1. Total Squads (Tetap)
            'player_count_total': total_players_in_squads, # 2. Total Players (BARU)
            'avg_age': global_avg_age,                  # 3. Avg Global Age (BARU)
        },
    }
    return render(request, 'dream_squad.html', context)

@login_required
def create_squad(request):
    if request.method == 'POST':
        form = DreamSquadForm(request.POST)
        if form.is_valid():
            try:
                squad = form.save(commit=False)
                squad.user = request.user
                squad.save()
                # Jika sukses, redirect ke detail atau list
                return redirect('dream_squad:squad_detail', squad_id=squad.id)
            except IntegrityError:
                # <--- INI BAGIAN PENTINGNYA
                # Jika nama kembar, tambahkan error ke field 'name'
                form.add_error('name', 'You already have a squad with this name. Please choose another.')
    else:
        form = DreamSquadForm()

    return render(request, 'squad_form.html', {'form': form})

# dream_squad/views.py (Hanya fungsi squad_detail)

@login_required
def squad_detail(request, squad_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    
    # Select related: agar data club dan player ditarik sekaligus
    dsp_qs = squad.players.select_related('player__club').all()
    squad_players = [dsp.player for dsp in dsp_qs]
    player_count = len(squad_players)

    # favorite_ids (player ids already in this squad) -> used by partial
    favorite_ids = {p.id for p in squad_players}

    # allow search in this page too
    query = (request.GET.get('q') or '').strip()
    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        players_qs = players_qs.filter(name__icontains=query)
    total_players = players_qs.count()
    players_qs = players_qs[:50]
    players = list(players_qs)
    limited = total_players > len(players)

    
    # --- PERHITUNGAN STATISTIK SQUAD BARU ---
    
    # List untuk rata-rata
    pass_accuracies = []
    xgs = []
    defensive_actions = [] # BARU: Untuk menghitung Rata-rata Defensive Action
    ages = []              # BARU: Untuk menghitung Rata-rata Usia
    
    # Total akumulatif
    total_goals = 0
    total_assists = 0
    
    unique_teams = set()
    
    for player in squad_players:
        # Distribution
        if getattr(player, 'pass_accuracy', None) is not None:
            pass_accuracies.append(player.pass_accuracy)

        # Offense Accumulative
        total_goals += getattr(player, 'goals', 0)
        total_assists += getattr(player, 'assists', 0)
        if getattr(player, 'xg', None) is not None:
            xgs.append(player.xg)

        # Defense (BARU: Ditambahkan ke list untuk rata-rata)
        tackles_won = getattr(player, 'tackles_won', 0) or 0
        clearances = getattr(player, 'clearances', 0) or 0
        defensive_actions.append(tackles_won + clearances)

        # Usia (BARU: Ditambahkan ke list untuk rata-rata)
        age = getattr(player, 'age', None)
        if age is not None and age > 0:
            ages.append(age)

        # Teams
        if player.club and getattr(player.club, 'name', None):
            unique_teams.add(player.club.name)

    # Hitung rata-rata
    squad_avg_pass = round(sum(pass_accuracies) / len(pass_accuracies)) if pass_accuracies else 0
    squad_avg_xg = round(sum(xgs) / len(xgs), 2) if xgs else 0 # 2 desimal
    squad_teams_count = len(unique_teams)
    
    # BARU: Perhitungan Rata-rata Defensive Action
    squad_avg_def_actions = round(sum(defensive_actions) / len(defensive_actions), 1) if defensive_actions else 0
    
    # BARU: Perhitungan Rata-rata Usia
    squad_avg_age = round(sum(ages) / len(ages), 1) if ages else 0 

    # Cek validasi untuk ditampilkan di UI
    is_valid = squad_has_required_positions(squad_players) and player_count <= MAX_PLAYERS

    context = {
        'squad': squad,
        'squad_players': squad_players,
        'players': players,
        'players_limited': limited,
        'search_query': query,
        'favorite_ids': favorite_ids,
        'MAX_PLAYERS': MAX_PLAYERS,

        # Statistik Baru untuk Detail Squad
        'squad_stats': {
            'player_count': player_count,
            'teams_count': squad_teams_count,
            'avg_pass': squad_avg_pass,
            'avg_xg': squad_avg_xg,
            'total_goals_assists': total_goals + total_assists,
            # PERUBAHAN: Menggunakan rata-rata, bukan total
            'avg_def_actions': squad_avg_def_actions, 
            # PERUBAHAN: Progressive Actions diganti Avg Age
            'avg_age': squad_avg_age, 
        },
        'is_squad_valid': is_valid, # Status validasi
    }
    return render(request, 'squad_detail.html', context)

@login_required
@require_POST
def add_player_to_squad(request, squad_id, player_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    player = get_object_or_404(Player, id=player_id)

    # if player already in squad: ok (idempotent)
    if squad.players.filter(player=player).exists():
        return JsonResponse({'success': True})

    if squad.players.count() >= MAX_PLAYERS:
        return JsonResponse({'success': False, 'error': 'Squad reached maximum of 22 players.'}, status=400)

    # add
    DreamSquadPlayer.objects.create(squad=squad, player=player)

    # post-add: optional: do not force required positions yet — allow user to build, but if you want to enforce right away, check below

    return JsonResponse({'success': True})

@login_required
@require_POST
def remove_player_from_squad(request, squad_id, player_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    player = get_object_or_404(Player, id=player_id)

    # check if removing would violate required positions
    remaining_players = [dsp.player for dsp in squad.players.select_related('player').all() if dsp.player.id != player.id]
    if not squad_has_required_positions(remaining_players):
        return JsonResponse({'success': False, 'error': 'Cannot remove player. Squad must include at least one GK, DF, MF, and FW.'}, status=400)

    squad.players.filter(player=player).delete()
    return JsonResponse({'success': True})

# dream_squad/views.py

MAX_PLAYERS = 22 # Pastikan konstanta ini ada di file Anda
# ... (impor lainnya) ...

@login_required
def edit_squad(request, squad_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    
    # --- 1. Ambil data pemain awal (seperti sebelumnya) ---
    initial_players = [dsp.player.id for dsp in squad.players.all()]
    squad_players_objects = list(Player.objects.filter(id__in=initial_players).select_related('club'))


    if request.method == 'POST':
        form = DreamSquadForm(request.POST, instance=squad)
        player_ids = request.POST.getlist('players') 
        
        if form.is_valid():
            # ... (Logika POST Anda untuk menyimpan form) ...
            
            # Jika berhasil, kita bisa redirect atau render ulang dengan data
            # Jika menggunakan render ulang, pastikan context lengkap
            if player_ids:
                # ... (Logika validasi & penyimpanan pemain) ...
                
                if form.errors:
                    # Jika ada error, render ulang dengan context lengkap
                    # Lanjutkan ke bagian render di bawah POST
                    pass
                else:
                    # Jika SUKSES (setelah form.save()), biasanya redirect ke detail
                    return redirect('dream_squad:squad_detail', squad_id=squad.id) # Lebih disarankan redirect
            
            else:
                # Jika hanya update nama squad (tanpa player_ids)
                form.save()
                return redirect('dream_squad:squad_detail', squad_id=squad.id)


    else:
        # GET Request: Memuat data form dan pemain
        form = DreamSquadForm(instance=squad)
        
    
    # --- 2. Tambahkan Logika Discover Player (Search) ---
    
    query = (request.GET.get('q') or '').strip()
    
    # Memuat semua pemain atau hasil pencarian
    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        # Filter jika ada query
        players_qs = players_qs.filter(name__icontains=query)
        
    total_players = players_qs.count()
    # Batasi jumlah pemain yang ditampilkan
    players_qs = players_qs[:50] 
    players_discovery = list(players_qs)
    limited = total_players > len(players_discovery)
    
    # favorite_ids di sini adalah pemain yang sudah ada di squad ini (untuk tombol Add/Remove)
    favorite_ids = set(initial_players)


    # --- 3. Render Template dengan Context Lengkap ---
    context = {
        'form': form,
        'squad': squad,
        'initial_players': initial_players, # ID pemain yang sudah ada (untuk form hidden)
        'squad_players': squad_players_objects, # Objek pemain yang sudah ada (optional)
        
        # Variabel untuk Discover Section
        'players': players_discovery,      # Daftar pemain yang akan ditampilkan
        'players_limited': limited,
        'search_query': query,
        'favorite_ids': favorite_ids,      # Pemain yang sudah ada di squad ini
    }

    return render(request, 'squad_form.html', context)

@login_required
@require_POST
def delete_squad(request, squad_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    squad.delete()
    return redirect('dream_squad:dream_squad')

# dream_squad/views.py (Dalam fungsi select_squad_for_player)

@login_required
def select_squad_for_player(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    
    # 1. ANOTASI SQUADS (untuk menghitung player_count saat ini)
    squads = DreamSquad.objects.filter(user=request.user).annotate(
        player_count=Count('players') 
    )

    # =======================================================
    # LOGIKA POST (Penambahan Pemain)
    # =======================================================
    if request.method == 'POST':
        squad_id = request.POST.get('squad_id')
        
        # 1. Validasi ID Squad
        if not squad_id:
            error_message = 'Please select a squad to add the player to.'
            # Lanjutkan ke return error di akhir blok POST
        else:
            try:
                # Dapatkan squad dari database, pastikan milik user yang login
                selected_squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
                
                # Gunakan hitungan dari anotasi untuk validasi cepat
                current_player_count = squads.get(id=squad_id).player_count
                
                # 2. Validasi Batas Maksimum Pemain
                if current_player_count >= MAX_PLAYERS:
                    error_message = f'Squad {selected_squad.name} is full (Max {MAX_PLAYERS} players).'
                
                # 3. Validasi Duplikasi Pemain (Optional, tapi disarankan)
                elif selected_squad.players.filter(id=player.id).exists():
                    # Jika pemain sudah ada, anggap sukses dan redirect
                    return redirect('dream_squad:squad_detail', squad_id=selected_squad.id)
                
                # 4. EKSEKUSI PENAMBAHAN (Jika semua validasi lulus)
                else:
                # Menggunakan model perantara untuk menambahkan hubungan
                    DreamSquadPlayer.objects.create(
                        squad=selected_squad, 
                        player=player
                        # Tambahkan field lain jika model DreamSquadPlayer Anda memilikinya (misalnya, date_added=timezone.now())
                    ) 
                    
                    # Redirect ke halaman detail squad setelah sukses
                    return redirect('dream_squad:squad_detail', squad_id=selected_squad.id)

            except DreamSquad.DoesNotExist:
                error_message = 'Selected squad not found or does not belong to you.'
            except Exception as e:
                error_message = f'An unexpected error occurred: {e}'


        # Jika ada error, re-render form dengan pesan error
        # Kita harus memastikan `squads` memiliki properti `is_full` untuk re-render
        for squad in squads:
             squad.is_full = squad.player_count >= MAX_PLAYERS
             
        return render(request, 'select_squad.html', {
            'player': player,
            'squads': squads,
            'MAX_PLAYERS': MAX_PLAYERS,
            'error': error_message, # <-- Menampilkan pesan error
        })
    # =======================================================
    # LOGIKA GET (Menampilkan Form)
    # =======================================================
    # Tandai setiap squad dengan status 'is_full'
    for squad in squads:
        squad.is_full = squad.player_count >= MAX_PLAYERS
    
    # Mengembalikan tampilan awal
    return render(request, 'select_squad.html', {
        'player': player,
        'squads': squads,
        'MAX_PLAYERS': MAX_PLAYERS,
    })

@login_required
def player_detail(request, player_id):
    """Menampilkan statistik detail untuk pemain tertentu."""
    # Ambil objek Player, atau tampilkan 404 jika tidak ditemukan
    player = get_object_or_404(Player.objects.select_related('club'), id=player_id)
    
    # Anda bisa menghitung statistik tambahan di sini jika perlu
    
    context = {
        'player': player,
    }
    return render(request, 'player_detail.html', context) # MERENDER TEMPLATE BARU