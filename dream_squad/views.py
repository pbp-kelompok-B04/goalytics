# views.py
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .models import BannedWord, DreamSquad, DreamSquadPlayer
from django.contrib import messages
from django.urls import reverse
from django.template.loader import render_to_string

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
    """Show list of user's squads + Global Admin Stats + Banned Words Management."""
    query = (request.GET.get('q') or '').strip()

    # --- LOGIKA ROLE ADMIN ---
    is_admin = (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.role == 'admin')

    # --- 1. FITUR BANNED WORDS (ADMIN ONLY) ---
    banned_words = []
    if is_admin:
        # Logika Tambah Kata Terlarang via POST
        if request.method == 'POST' and 'add_banned_word' in request.POST:
            word_to_ban = request.POST.get('word', '').strip().lower()
            if word_to_ban:
                # get_or_create mencegah duplikasi kata yang sama
                obj, created = BannedWord.objects.get_or_create(word=word_to_ban)
                if created:
                    messages.success(request, f"Kata '{word_to_ban}' berhasil diblokir.")
                else:
                    messages.info(request, f"Kata '{word_to_ban}' sudah ada dalam daftar blokir.")
            return redirect('dream_squad:dream_squad') # Refresh agar tidak double post

        # Ambil daftar kata untuk ditampilkan
        banned_words = BannedWord.objects.all().order_by('-added_at')

    # --- 2. AMBIL SQUADS & STATS ---
    if is_admin:
        # Admin melihat SEMUA squad untuk statistik global
        squads_all = DreamSquad.objects.all().prefetch_related('players__player')
        user_squads = squads_all.filter(user=request.user)
    else:
        user_squads = DreamSquad.objects.filter(user=request.user).prefetch_related('players__player')
        squads_all = user_squads

    # Hitung Statistik Global (untuk kartu di atas)
    total_squads_count = squads_all.count()
    total_players_in_all_squads = DreamSquadPlayer.objects.count()
    avg_age = Player.objects.filter(in_dream_squads__isnull=False).aggregate(Avg('age'))['age__avg'] or 0

    # --- 3. LOGIKA PLAYER PALING POPULER (ADMIN ONLY) ---
    most_popular_players = []
    if is_admin:
        most_popular_players = Player.objects.annotate(
            usage_count=Count('in_dream_squads')
        ).filter(usage_count__gt=0).order_by('-usage_count')[:5]

    # --- 4. SEARCH PLAYERS (DISCOVERY SECTION) ---
    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        players_qs = players_qs.filter(name__icontains=query)

    total_players_search_count = players_qs.count()
    players_discovery = list(players_qs[:50])
    limited = total_players_search_count > len(players_discovery)

    # --- 5. CONTEXT & RENDER ---
    context = {
        'squads': user_squads,
        'squad_stats': {
            'count': total_squads_count,
            'player_count_total': total_players_in_all_squads,
            'avg_age': round(avg_age, 1),
        },
        'players': players_discovery,
        'players_limited': limited,
        'is_admin': is_admin,
        'most_popular_players': most_popular_players,
        'banned_words': banned_words, # Kirim daftar kata ke template
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Kita merender hanya bagian kartu pemain ke dalam string
            html = render_to_string('partials/player_results.html', context, request=request)
            # Kirim sebagai JSON
            return JsonResponse({'html': html})

    return render(request, 'dream_squad.html', context)

@login_required
def create_squad(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        form = DreamSquadForm(request.POST)
        if form.is_valid():
            # --- VALIDASI BANNED WORDS ---
            squad_name_input = form.cleaned_data.get('name', '').lower()
            banned_queries = BannedWord.objects.values_list('word', flat=True)
            
            for bad_word in banned_queries:
                if bad_word.lower() in squad_name_input:
                    error_msg = f"The name contains a restricted word: '{bad_word}'."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_msg}, status=400)
                    form.add_error('name', error_msg)
                    return render(request, 'squad_form.html', {'form': form})

            # --- PROSES SIMPAN ---
            try:
                squad = form.save(commit=False)
                squad.user = request.user
                squad.save()
                
                # Membuat URL detail secara dinamis sesuai urls.py Anda
                # Hasilnya akan menjadi: /dream-squad/4/ (sesuai ID-nya)
                redirect_path = reverse('dream_squad:squad_detail', kwargs={'squad_id': squad.id})
                
                msg = f"Squad '{squad.name}' has been created successfully!"
                
                if is_ajax:
                    return JsonResponse({
                        'success': True, 
                        'message': msg,
                        'redirect_url': redirect_path 
                    })
                
                messages.success(request, msg)
                return redirect(redirect_path)
                
            except IntegrityError:
                error_msg = 'You already have a squad with this name. Please choose another.'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                form.add_error('name', error_msg)
        else:
            if is_ajax:
                # Mengambil error pertama dari form jika ada error validasi lain
                first_error = form.errors.as_text()
                return JsonResponse({'success': False, 'error': "Invalid data."}, status=400)
    else:
        form = DreamSquadForm()

    if is_ajax:
        html = render_to_string('partials/create_squad_modal_content.html', {'form': form}, request=request)
        return JsonResponse({'html': html})

    return render(request, 'squad_form.html', {'form': form})

# dream_squad/views.py (Hanya fungsi squad_detail)
@login_required
def squad_detail(request, squad_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    # 1. Ambil data pemain yang sudah ada di squad
    dsp_qs = squad.players.select_related('player__club').all()
    squad_players = [dsp.player for dsp in dsp_qs]
    player_count = len(squad_players)
    favorite_ids = {p.id for p in squad_players}
    
    # Status apakah squad penuh (Digunakan untuk menonaktifkan tombol ADD di partial)
    is_squad_full = player_count >= MAX_PLAYERS

    # 2. Logika Pencarian Pemain (Discover Players)
    query = (request.GET.get('q') or '').strip()
    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        players_qs = players_qs.filter(name__icontains=query)
    
    total_players = players_qs.count()
    players_qs = players_qs[:50]
    players = list(players_qs)
    limited = total_players > len(players)

    # --- JIKA REQUEST ADALAH AJAX (Pencarian Real-time) ---
    if is_ajax:
        html = render_to_string('partials/player_results.html', {
            'players': players,
            'favorite_ids': favorite_ids,
            'players_limited': limited,
            'is_squad_full': is_squad_full, # Kirim status penuh ke partial
        }, request=request)
        return JsonResponse({'html': html})

    # 3. --- PERHITUNGAN STATISTIK SQUAD (Hanya dijalankan jika bukan AJAX) ---
    pass_accuracies = []
    xgs = []
    defensive_actions = [] 
    ages = []
    total_goals = 0
    total_assists = 0
    unique_teams = set()
    
    for player in squad_players:
        if getattr(player, 'pass_accuracy', None) is not None:
            pass_accuracies.append(player.pass_accuracy)

        total_goals += getattr(player, 'goals', 0)
        total_assists += getattr(player, 'assists', 0)
        if getattr(player, 'xg', None) is not None:
            xgs.append(player.xg)

        tackles_won = getattr(player, 'tackles_won', 0) or 0
        clearances = getattr(player, 'clearances', 0) or 0
        defensive_actions.append(tackles_won + clearances)

        age = getattr(player, 'age', None)
        if age is not None and age > 0:
            ages.append(age)

        if player.club and getattr(player.club, 'name', None):
            unique_teams.add(player.club.name)

    # Hitung rata-rata
    squad_avg_pass = round(sum(pass_accuracies) / len(pass_accuracies)) if pass_accuracies else 0
    squad_avg_xg = round(sum(xgs) / len(xgs), 2) if xgs else 0
    squad_avg_def_actions = round(sum(defensive_actions) / len(defensive_actions), 1) if defensive_actions else 0
    squad_avg_age = round(sum(ages) / len(ages), 1) if ages else 0 

    # Cek validasi posisi
    is_valid = squad_has_required_positions(squad_players) and player_count <= MAX_PLAYERS

    context = {
        'squad': squad,
        'squad_players': squad_players,
        'players': players,
        'players_limited': limited,
        'search_query': query,
        'favorite_ids': favorite_ids,
        'MAX_PLAYERS': MAX_PLAYERS,
        'is_squad_full': is_squad_full,
        'squad_stats': {
            'player_count': player_count,
            'teams_count': len(unique_teams),
            'avg_pass': squad_avg_pass,
            'avg_xg': squad_avg_xg,
            'total_goals_assists': total_goals + total_assists,
            'avg_def_actions': squad_avg_def_actions, 
            'avg_age': squad_avg_age, 
        },
        'is_squad_valid': is_valid,
    }
    return render(request, 'squad_detail.html', context)

@login_required
@require_POST
def add_player_to_squad(request, squad_id, player_id):
    if request.method == 'POST':
        squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
        player = get_object_or_404(Player, id=player_id)
        
        # 1. Cek apakah pemain sudah ada di squad ini
        if squad.players.filter(player=player).exists():
            return JsonResponse({
                'success': False, 
                'error': f'{player.name} is already in this squad.'
            }, status=400)
        
        # 2. Cek kapasitas (MAX_PLAYERS)
        if squad.players.count() >= 22: # Ganti 22 dengan variable MAX_PLAYERS Anda
            return JsonResponse({
                'success': False, 
                'error': 'This squad is full (max 22 players).'
            }, status=400)
        
        # 3. Tambahkan pemain
        # Sesuaikan dengan model M2M Anda (misal: DreamSquadPlayer)
        DreamSquadPlayer.objects.create(squad=squad, player=player)
        
        return JsonResponse({
            'success': True,
            'message': f'Added {player.name} to {squad.name}!',
            'player_count': squad.players.count()
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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
def delete_squad(request, squad_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    
    if request.method == 'POST':
        squad_name = squad.name
        squad.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Squad "{squad_name}" has been deleted.'
            })
            
        messages.success(request, f'Squad "{squad_name}" deleted.')
        return redirect('dream_squad:dream_squad')
        
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)

@login_required
def select_squad_for_player(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    error_message = None
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    # 1. Ambil squads dengan anotasi jumlah pemain saat ini
    squads = DreamSquad.objects.filter(user=request.user).annotate(
        player_count=Count('players') 
    )

    if request.method == 'POST':
        squad_id = request.POST.get('squad_id')
        
        if not squad_id:
            error_message = 'Please select a squad to add the player to.'
        else:
            try:
                selected_squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
                current_squad_info = squads.get(id=squad_id)
                
                # A. Validasi Duplikasi
                if DreamSquadPlayer.objects.filter(squad=selected_squad, player=player).exists():
                    error_message = f'Pemain {player.name} sudah terdaftar di squad {selected_squad.name}.'
                
                # B. Validasi Batas Maksimum
                elif current_squad_info.player_count >= MAX_PLAYERS:
                    error_message = f'Squad {selected_squad.name} sudah penuh (Maksimal {MAX_PLAYERS} pemain).'
                
                # C. Eksekusi Penambahan
                else:
                    DreamSquadPlayer.objects.create(
                        squad=selected_squad, 
                        player=player
                    )
                    
                    # Jika AJAX, kirim JSON sukses (bukan redirect)
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': f'Berhasil menambahkan {player.name} ke {selected_squad.name}!'
                        })
                    
                    return redirect('dream_squad:squad_detail', squad_id=selected_squad.id)

            except DreamSquad.DoesNotExist:
                error_message = 'Selected squad not found.'
            except Exception as e:
                error_message = f'Gagal menambahkan pemain: {str(e)}'

        # Jika terjadi error saat POST melalui AJAX
        if is_ajax and error_message:
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)

    # --- Persiapan untuk Rendering ---
    
    # Tandai status 'is_full' dan 'has_player' untuk membantu UI
    for squad in squads:
        squad.is_full = squad.player_count >= MAX_PLAYERS
        squad.has_player = DreamSquadPlayer.objects.filter(squad=squad, player=player).exists()
    
    context = {
        'player': player,
        'squads': squads,
        'MAX_PLAYERS': MAX_PLAYERS,
        'error': error_message,
    }

    # Jika request AJAX, render template partial (tanpa base.html)
    if is_ajax:
        html = render_to_string('partials/select_squad_modal_content.html', context, request=request)
        return JsonResponse({'html': html})

    # Fallback untuk request normal (synchronous)
    return render(request, 'select_squad.html', context)

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