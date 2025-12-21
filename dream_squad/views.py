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
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
import json
from PlayerClub_Data.models import Player
from .models import DreamSquad, DreamSquadPlayer
from .forms import DreamSquadForm
import traceback

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

@require_http_methods(["GET"])
def squad_list_api(request):
    """API Version - Mengikuti pola stabil untuk Flutter"""
    try:
        # 1. Ambil Parameter Search
        query = (request.GET.get('q') or '').strip()

        # 2. Cek Role Admin (Tanpa melempar error jika user belum login)
        is_authenticated = request.user.is_authenticated
        is_admin = False
        if is_authenticated and hasattr(request.user, 'profile'):
            is_admin = (request.user.profile.role == 'admin')

        # 3. Logika Squad
        # Jika tidak login, user_squads kosong saja (jangan return 403 HTML)
        if not is_authenticated:
            user_squads = []
            squads_all_count = 0 # Statistik global tetap bisa diakses
        elif is_admin:
            user_squads = DreamSquad.objects.filter(user=request.user)
            squads_all = DreamSquad.objects.all()
            squads_all_count = squads_all.count()
        else:
            user_squads = DreamSquad.objects.filter(user=request.user)
            squads_all_count = user_squads.count()

        # 4. Statistik (Global Data)
        total_players_in_all_squads = DreamSquadPlayer.objects.count()
        avg_age_data = Player.objects.filter(in_dream_squads__isnull=False).aggregate(Avg('age'))
        avg_age = avg_age_data['age__avg'] or 0

        # 5. Serialisasi My Squads
        user_squads_list = []
        for s in user_squads:
            user_squads_list.append({
                'id': s.id,
                'name': s.name,
                'player_count': s.players.count()
            })

        # 6. Search Players (Discovery Section)
        players_qs = Player.objects.select_related('club').order_by('name')
        if query:
            players_qs = players_qs.filter(name__icontains=query)
        
        discovery_list = []
        for p in players_qs[:50]:
            discovery_list.append({
                'id': p.id,
                'name': p.name,
                'position': p.position,
                'club_name': p.club.name if p.club else "No Club",
                'age': p.age
            })

        # 7. Admin Extras
        admin_data = {'banned_words': [], 'popular_players': []}
        if is_admin:
            admin_data['banned_words'] = list(BannedWord.objects.values_list('word', flat=True))
            most_popular = Player.objects.annotate(usage=Count('in_dream_squads')).filter(usage__gt=0).order_by('-usage')[:5]
            admin_data['popular_players'] = [{'id':p.id, 'name':p.name, 'usage':p.usage} for p in most_popular]

        # 8. RETURN SUCCESS RESPONSE
        return JsonResponse({
            'success': True,
            'is_admin': is_admin,
            'my_squads': user_squads_list,
            'discovery_players': discovery_list,
            'stats': {
                'total_squads': squads_all_count,
                'total_players_used': total_players_in_all_squads,
                'average_age': round(float(avg_age), 1),
            },
            'admin_extras': admin_data
        })

    except Exception as e:
        # Jika ada error koding/database, kirim JSON, bukan HTML error 500
        print(traceback.format_exc()) # Muncul di terminal server
        return JsonResponse({
            'success': False,
            'error': str(e),
            'my_squads': [],
            'discovery_players': []
        }, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def add_banned_word_api(request):
    """API khusus Admin untuk menambah kata terlarang via Flutter"""
    try:
        # 1. Cek Admin
        if not request.user.is_authenticated or request.user.profile.role != 'admin':
            return JsonResponse({'success': False, 'error': 'Unauthorized. Admin only.'}, status=403)

        # 2. Parse Data
        data = json.loads(request.body)
        word_to_ban = data.get('word', '').strip().lower()

        if not word_to_ban:
            return JsonResponse({'success': False, 'error': 'Word cannot be empty.'}, status=400)

        # 3. Simpan
        obj, created = BannedWord.objects.get_or_create(word=word_to_ban)
        
        if created:
            return JsonResponse({
                'success': True, 
                'message': f"Kata '{word_to_ban}' berhasil diblokir."
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': f"Kata '{word_to_ban}' sudah ada di daftar."
            }, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def create_squad(request):
    """
    Versi Hybrid: Mendukung Web (Normal & AJAX) serta Flutter API.
    Meniru pola teman Anda: Cek login manual & Try-Except menyeluruh.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    # Identifikasi jika request datang dari Flutter (biasanya tidak membawa header XMLHttpRequest)
    is_flutter = not is_ajax and (request.content_type == 'application/json' or 'flutter' in request.headers.get('User-Agent', '').lower())

    try:
        # --- 1. CEK LOGIN MANUAL (Agar Flutter dapat JSON 401, bukan HTML Login) ---
        if not request.user.is_authenticated:
            if is_ajax or is_flutter:
                return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=401)
            return redirect('login')  # Normal web redirect

        if request.method == 'POST':
            # --- 2. PARSING DATA (Support Form Data & JSON Body) ---
            if is_flutter:
                try:
                    data = json.loads(request.body)
                    squad_name_input = data.get('name', '')
                    player_ids = data.get('mandatory_players', [])
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Invalid JSON format.'}, status=400)
            else:
                squad_name_input = request.POST.get('name', '')
                player_ids = request.POST.getlist('mandatory_players')

            # --- 3. VALIDASI BANNED WORDS ---
            banned_queries = BannedWord.objects.values_list('word', flat=True)
            for bad_word in banned_queries:
                if bad_word.lower() in squad_name_input.lower():
                    error_msg = f"The name contains a restricted word: '{bad_word}'."
                    if is_ajax or is_flutter:
                        return JsonResponse({'success': False, 'error': error_msg}, status=400)
                    # Fallback untuk web normal
                    form = DreamSquadForm(request.POST)
                    form.add_error('name', error_msg)
                    return render(request, 'squad_form.html', {'form': form})

            # --- 4. VALIDASI PEMAIN ---
            selected_players = Player.objects.filter(id__in=player_ids)
            if len(player_ids) < 4 or not squad_has_required_positions(list(selected_players)):
                error_msg = "Selection incomplete. You need at least 1 GK, 1 DF, 1 MF, and 1 FW."
                if is_ajax or is_flutter:
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                
                form = DreamSquadForm(request.POST)
                form.add_error(None, error_msg)
                return render(request, 'squad_form.html', {'form': form})

            # --- 5. PROSES SIMPAN (ATOMIC) ---
            try:
                with transaction.atomic():
                    # Jika Flutter, kita buat manual. Jika Web, pakai Form.
                    if is_flutter:
                        squad = DreamSquad.objects.create(user=request.user, name=squad_name_input)
                    else:
                        form = DreamSquadForm(request.POST)
                        if not form.is_valid():
                             return JsonResponse({'success': False, 'error': 'Invalid form data.'}, status=400)
                        squad = form.save(commit=False)
                        squad.user = request.user
                        squad.save()

                    new_players = [
                        DreamSquadPlayer(squad=squad, player=p) for p in selected_players
                    ]
                    DreamSquadPlayer.objects.bulk_create(new_players)
                
                # RESPONSE SUKSES
                redirect_path = reverse('dream_squad:squad_detail', kwargs={'squad_id': squad.id})
                msg = f"Squad '{squad.name}' created successfully!"
                
                if is_ajax or is_flutter:
                    return JsonResponse({
                        'success': True, 
                        'message': msg,
                        'squad_id': squad.id,
                        'redirect_url': redirect_path 
                    })
                
                messages.success(request, msg)
                return redirect(redirect_path)

            except IntegrityError:
                error_msg = 'You already have a squad with this name.'
                if is_ajax or is_flutter:
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                form = DreamSquadForm(request.POST)
                form.add_error('name', error_msg)
                return render(request, 'squad_form.html', {'form': form})

        # --- 6. HANDLE GET REQUEST ---
        else:
            form = DreamSquadForm()

        players_by_pos = {
            'GK': Player.objects.filter(position='GK').order_by('name'),
            'DF': Player.objects.filter(position='DF').order_by('name'),
            'MF': Player.objects.filter(position='MF').order_by('name'),
            'FW': Player.objects.filter(position='FW').order_by('name'),
        }

        if is_ajax:
            html = render_to_string('partials/create_squad_modal_content.html', {
                'form': form,
                'players_by_pos': players_by_pos
            }, request=request)
            return JsonResponse({'html': html})

        return render(request, 'squad_form.html', {'form': form, 'players_by_pos': players_by_pos})

    except Exception as e:
        # Menangkap error tak terduga (Penyebab utama FormatException di Flutter)
        print(traceback.format_exc()) # Debug di terminal
        if is_ajax or is_flutter:
            return JsonResponse({'success': False, 'error': f'Server Error: {str(e)}'}, status=500)
        raise e # Web normal biarkan Django handle

@csrf_exempt
@require_http_methods(["POST"])
def create_squad_api(request):
    """API untuk membuat squad - Mengikuti pola stabil teman Anda"""
    try:
        # 1. Pastikan User Login (Manual check agar return JSON, bukan HTML)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False, 
                'error': 'Authentication required. Please login first.'
            }, status=401)

        # 2. Parsing Data
        try:
            data = json.loads(request.body)
            squad_name = data.get('name', '').strip()
            player_ids = data.get('mandatory_players', [])
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format.'}, status=400)

        # 3. Validasi Nama
        if not squad_name:
            return JsonResponse({'success': False, 'error': 'Squad name is required.'}, status=400)

        # 4. Validasi Banned Words
        banned_words = BannedWord.objects.values_list('word', flat=True)
        for word in banned_words:
            if word.lower() in squad_name.lower():
                return JsonResponse({
                    'success': False, 
                    'error': f"Contains restricted word: '{word}'."
                }, status=400)

        # 5. Validasi Pemain
        selected_players = Player.objects.filter(id__in=player_ids)
        
        # Logika validasi posisi (Pastikan fungsi squad_has_required_positions tersedia)
        if selected_players.count() < 4 or not squad_has_required_positions(list(selected_players)):
            return JsonResponse({
                'success': False,
                'error': 'Selection incomplete. You need at least 1 GK, 1 DF, 1 MF, and 1 FW.'
            }, status=400)

        # 6. Simpan Squad (Atomic)
        try:
            with transaction.atomic():
                squad = DreamSquad.objects.create(user=request.user, name=squad_name)
                
                new_players_relation = [
                    DreamSquadPlayer(squad=squad, player=p) for p in selected_players
                ]
                DreamSquadPlayer.objects.bulk_create(new_players_relation)
            
            return JsonResponse({
                'success': True,
                'message': f"Squad '{squad.name}' created successfully!",
                'squad_id': squad.id,
                'name': squad.name
            })
            
        except IntegrityError:
            return JsonResponse({
                'success': False, 
                'error': 'You already have a squad with this exact name.'
            }, status=400)

    except Exception as e:
        # Menangkap error tak terduga (Internal Server Error)
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }, status=500)
    
@require_http_methods(["GET"])
def get_players_for_modal(request):
    """API khusus untuk mengisi dropdown modal Flutter tanpa limit abjad"""
    try:
        # Kita ambil SEMUA pemain dan kelompokkan di server agar Flutter tinggal pakai
        data = {
            'success': True,
            'players_by_pos': {
                'GK': list(Player.objects.filter(position='GK').order_by('name').values('id', 'name')),
                'DF': list(Player.objects.filter(position='DF').order_by('name').values('id', 'name')),
                'MF': list(Player.objects.filter(position='MF').order_by('name').values('id', 'name')),
                'FW': list(Player.objects.filter(position='FW').order_by('name').values('id', 'name')),
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
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

@require_http_methods(["GET"])
def squad_detail_api(request, squad_id):
    """API Version - Mengikuti pola stabil teman Anda untuk Flutter"""
    try:
        # 1. Cek Autentikasi Manual (Mencegah Redirect HTML)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Silakan login terlebih dahulu.'
            }, status=401)

        # 2. Ambil Data Squad
        # Menggunakan try-except manual agar return JSON jika 404
        try:
            squad = DreamSquad.objects.get(id=squad_id, user=request.user)
        except DreamSquad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Squad tidak ditemukan atau Anda tidak memiliki akses.'
            }, status=404)

        # 3. Ambil Pemain di Squad
        dsp_qs = squad.players.select_related('player__club').all()
        squad_players = [dsp.player for dsp in dsp_qs]
        favorite_ids = [p.id for p in squad_players]
        
        # 4. Logika Pencarian Pemain (Discovery)
        query = (request.GET.get('q') or '').strip()
        players_qs = Player.objects.select_related('club').order_by('name')
        if query:
            players_qs = players_qs.filter(name__icontains=query)
        
        total_players_found = players_qs.count()
        discovery_players = players_qs[:50]

        # 5. Perhitungan Statistik
        stats_data = {
            'pass_accs': [], 'xgs': [], 'def_actions': [], 'ages': [],
            'goals': 0, 'assists': 0, 'teams': set()
        }

        for p in squad_players:
            if getattr(p, 'pass_accuracy', None) is not None:
                stats_data['pass_accs'].append(p.pass_accuracy)
            
            stats_data['goals'] += getattr(p, 'goals', 0)
            stats_data['assists'] += getattr(p, 'assists', 0)
            
            if getattr(p, 'xg', None) is not None:
                stats_data['xgs'].append(float(p.xg))

            stats_data['def_actions'].append(
                (getattr(p, 'tackles_won', 0) or 0) + (getattr(p, 'clearances', 0) or 0)
            )

            age = getattr(p, 'age', 0)
            if age > 0: stats_data['ages'].append(age)
            if p.club: stats_data['teams'].add(p.club.name)

        # Final Stat Calculation
        n = len(squad_players)
        # MAX_PLAYERS didefinisikan secara lokal jika tidak ada di settings
        MAX_CAP = 15 

        # 6. Serialisasi Data Pemain
        current_players_list = [{
            'id': p.id,
            'name': p.name,
            'position': p.position,
            'club_name': p.club.name if p.club else "No Club",
            'goals': getattr(p, 'goals', 0),
            'assists': getattr(p, 'assists', 0),
            'image_url': p.image.url if hasattr(p, 'image') and p.image else None,
        } for p in squad_players]

        discovery_list = [{
            'id': p.id,
            'name': p.name,
            'position': p.position,
            'club_name': p.club.name if p.club else "No Club",
            'is_already_added': p.id in favorite_ids,
            'image_url': p.image.url if hasattr(p, 'image') and p.image else None,
        } for p in discovery_players]

        # 7. RETURN SUCCESS RESPONSE (Struktur Flat)
        return JsonResponse({
            'success': True,
            'squad_info': {
                'id': squad.id,
                'name': squad.name,
                'is_valid': squad_has_required_positions(squad_players) and n <= MAX_CAP,
                'is_full': n >= MAX_CAP,
            },
            'squad_stats': {
                'player_count': n,
                'teams_count': len(stats_data['teams']),
                'avg_pass': round(sum(stats_data['pass_accs']) / len(stats_data['pass_accs'])) if stats_data['pass_accs'] else 0,
                'avg_xg': round(sum(stats_data['xgs']) / len(stats_data['xgs']), 2) if stats_data['xgs'] else 0,
                'total_goals_assists': stats_data['goals'] + stats_data['assists'],
                'avg_def_actions': round(sum(stats_data['def_actions']) / len(stats_data['def_actions']), 1) if stats_data['def_actions'] else 0,
                'avg_age': round(sum(stats_data['ages']) / len(stats_data['ages']), 1) if stats_data['ages'] else 0,
                'max_capacity': MAX_CAP
            },
            'current_players': current_players_list,
            'discovery_players': discovery_list,
            'total_found': total_players_found
        })

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f"Terjadi kesalahan server: {str(e)}"
        }, status=500)

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

@csrf_exempt
@require_http_methods(["POST"])
def add_player_to_squad_api(request, squad_id, player_id):
    """API untuk menambah pemain - Mengikuti pola stabil untuk Flutter"""
    try:
        # 1. Cek Autentikasi Manual (Mencegah Redirect HTML 302)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Sesi berakhir, silakan login kembali.'
            }, status=401)

        # 2. Ambil Data (Manual check agar return JSON jika 404)
        try:
            squad = DreamSquad.objects.get(id=squad_id, user=request.user)
        except DreamSquad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Squad tidak ditemukan atau Anda tidak memiliki akses.'
            }, status=404)

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Pemain tidak ditemukan dalam database.'
            }, status=404)

        # 3. Cek Duplikasi
        if DreamSquadPlayer.objects.filter(squad=squad, player=player).exists():
            return JsonResponse({
                'success': False,
                'error': f'{player.name} sudah ada di dalam squad ini.'
            }, status=400)

        # 4. Cek Kapasitas
        MAX_PLAYERS = 15 # Sesuaikan dengan variabel global Anda
        current_count = squad.players.count()
        if current_count >= MAX_PLAYERS:
            return JsonResponse({
                'success': False,
                'error': f'Squad sudah penuh (maksimal {MAX_PLAYERS} pemain).'
            }, status=400)

        # 5. Eksekusi Penambahan
        DreamSquadPlayer.objects.create(squad=squad, player=player)
        
        # 6. Return Success Response (Struktur Flat)
        return JsonResponse({
            'success': True,
            'message': f'{player.name} berhasil ditambahkan ke {squad.name}!',
            'player_count': current_count + 1,
            'player_name': player.name,
            'squad_name': squad.name
        })

    except Exception as e:
        # Log error di console server untuk debugging
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Internal Server Error: {str(e)}'
        }, status=500)

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

@csrf_exempt
@require_http_methods(["POST"])
def remove_player_from_squad_api(request, squad_id, player_id):
    """API Version - Mengikuti pola stabil untuk menghapus pemain dari squad."""
    try:
        # 1. Cek Autentikasi Manual (Mencegah Redirect HTML 302)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Sesi berakhir, silakan login kembali.'
            }, status=401)

        # 2. Ambil Data (Cek keberadaan objek secara manual untuk return JSON)
        try:
            squad = DreamSquad.objects.get(id=squad_id, user=request.user)
        except DreamSquad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Squad tidak ditemukan atau akses ditolak.'
            }, status=404)

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Pemain tidak ditemukan.'
            }, status=404)

        # 3. Validasi Aturan Posisi Sebelum Menghapus
        dsp_qs = squad.players.select_related('player').all()
        # Hitung pemain yang tersisa jika penghapusan dilakukan
        remaining_players = [dsp.player for dsp in dsp_qs if dsp.player.id != player.id]
        
        # Menggunakan fungsi pembantu milikmu
        if not squad_has_required_positions(remaining_players):
            return JsonResponse({
                'success': False,
                'error': 'Gagal menghapus: Squad harus menyisakan minimal 1 GK, DF, MF, dan FW.'
            }, status=400)

        # 4. Proses Penghapusan
        deleted_count, _ = squad.players.filter(player=player).delete()
        
        if deleted_count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Pemain tersebut memang tidak ada di dalam squad ini.'
            }, status=404)

        # 5. Return Success Response (Flat Structure)
        return JsonResponse({
            'success': True,
            'message': f'{player.name} berhasil dihapus dari {squad.name}.',
            'player_count': len(remaining_players)
        })

    except Exception as e:
        # Log error ke terminal server untuk debugging
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Internal Server Error: {str(e)}'
        }, status=500)

@login_required
def edit_squad(request, squad_id):
    squad = get_object_or_404(DreamSquad, id=squad_id, user=request.user)
    
    # Ambil data pemain awal untuk ditampilkan di roster kiri
    initial_players = [dsp.player.id for dsp in squad.players.all()]
    squad_players_objects = list(Player.objects.filter(id__in=initial_players).select_related('club'))

    if request.method == 'POST':
        form = DreamSquadForm(request.POST, instance=squad)
        player_ids = request.POST.getlist('players') 
        
        if form.is_valid():
            # --- LOGIKA VALIDASI POSISI ---
            # Ambil semua objek pemain yang dipilih dalam POST
            selected_players = Player.objects.filter(id__in=player_ids)
            
            # Buat set posisi yang ada (misal: {'GK', 'DF', 'MF'})
            positions_present = {p.position for p in selected_players}
            required_positions = {'GK', 'DF', 'MF', 'FW'}
            
            # Cek apakah semua posisi wajib ada
            is_valid_composition = required_positions.issubset(positions_present)

            if not is_valid_composition:
                # Jika tidak lengkap, kirim pesan error
                messages.error(request, "Squad invalid! Anda harus memiliki setidaknya satu pemain di setiap posisi (GK, DF, MF, FW).")
                # Lanjut ke bawah untuk me-render ulang form dengan data yang diinput
            else:
                # Simpan perubahan nama/form utama
                saved_squad = form.save()
                
                # Update Roster (Hapus yang lama, masukkan yang baru)
                # Catatan: Sesuaikan dengan model M2M atau model perantara Anda
                squad.players.all().delete() 
                for p_id in player_ids:
                    # Asumsi Anda menggunakan model perantara DreamSquadPlayer
                    DreamSquadPlayer.objects.create(squad=saved_squad, player_id=p_id)
                
                messages.success(request, f"Squad '{saved_squad.name}' berhasil diperbarui!")
                return redirect('dream_squad:squad_detail', squad_id=squad.id)

    else:
        form = DreamSquadForm(instance=squad)
    
    query = (request.GET.get('q') or '').strip()
    players_qs = Player.objects.select_related('club').order_by('name')
    if query:
        players_qs = players_qs.filter(name__icontains=query)
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('partials/player_results.html', {
            'players': players_qs[:50],
            'favorite_ids': set(player_ids) if request.method == 'POST' else set(initial_players)
        })
        return JsonResponse({'html': html})

    context = {
        'form': form,
        'squad': squad,
        'initial_players': player_ids if request.method == 'POST' else initial_players,
        'squad_players': selected_players if request.method == 'POST' else squad_players_objects,
        'players': players_qs[:50],
        'search_query': query,
        'favorite_ids': set(player_ids) if request.method == 'POST' else set(initial_players),
    }
    return render(request, 'squad_form.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def edit_squad_api(request, squad_id):
    """API untuk mengedit nama squad dan update pemain secara bulk."""
    try:
        # 1. Cek Autentikasi Manual (Mencegah Redirect HTML)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Sesi berakhir, silakan login kembali.'
            }, status=401)

        # 2. Ambil Squad (Cek keberadaan objek secara manual)
        try:
            squad = DreamSquad.objects.get(id=squad_id, user=request.user)
        except DreamSquad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Squad tidak ditemukan atau akses ditolak.'
            }, status=404)

        # 3. Parsing JSON Data
        try:
            data = json.loads(request.body)
            new_name = data.get('name', '').strip()
            player_ids = data.get('players', [])
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Format data JSON tidak valid.'
            }, status=400)

        # 4. Validasi Nama Baru & Banned Words
        if new_name:
            banned_words = BannedWord.objects.values_list('word', flat=True)
            for word in banned_words:
                if word.lower() in new_name.lower():
                    return JsonResponse({
                        'success': False, 
                        'error': f"Nama mengandung kata terlarang: '{word}'."
                    }, status=400)
            squad.name = new_name

        # 5. Validasi Update Pemain (Jika ada daftar pemain yang dikirim)
        new_players = []
        if player_ids:
            new_players = Player.objects.filter(id__in=player_ids)
            MAX_CAP = 15 # Sesuaikan dengan variabel global Anda

            if new_players.count() > MAX_CAP:
                return JsonResponse({
                    'success': False, 
                    'error': f"Terlalu banyak pemain. Maksimal adalah {MAX_CAP}."
                }, status=400)

            if not squad_has_required_positions(list(new_players)):
                return JsonResponse({
                    'success': False, 
                    'error': "Squad tidak valid. Harus ada minimal 1 GK, DF, MF, dan FW."
                }, status=400)

        # 6. Simpan Perubahan (Atomic Transaction)
        try:
            with transaction.atomic():
                squad.save()

                if player_ids:
                    # Hapus pemain lama dan masukkan yang baru
                    DreamSquadPlayer.objects.filter(squad=squad).delete()
                    new_dsp_objects = [
                        DreamSquadPlayer(squad=squad, player=p) for p in new_players
                    ]
                    DreamSquadPlayer.objects.bulk_create(new_dsp_objects)

            return JsonResponse({
                'success': True,
                'message': f"Squad '{squad.name}' berhasil diperbarui!",
                'squad_id': squad.id,
                'name': squad.name,
                'player_count': squad.players.count()
            })

        except IntegrityError:
            return JsonResponse({
                'success': False, 
                'error': 'Anda sudah memiliki squad dengan nama tersebut.'
            }, status=400)

    except Exception as e:
        # Log error ke terminal server
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'error': f"Terjadi kesalahan server: {str(e)}"
        }, status=500)

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

@csrf_exempt
@require_http_methods(["POST"])
def delete_squad_api(request, squad_id):
    """API Version - Mengikuti pola stabil untuk menghapus squad secara keseluruhan."""
    try:
        # 1. Cek Autentikasi Manual (Mencegah Redirect HTML 302 dari @login_required)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Sesi berakhir, silakan login kembali.'
            }, status=401)

        # 2. Ambil Data Squad (Cek manual agar return JSON jika tidak ada)
        try:
            squad = DreamSquad.objects.get(id=squad_id, user=request.user)
        except DreamSquad.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Squad tidak ditemukan atau Anda tidak memiliki akses untuk menghapusnya.'
            }, status=404)

        # 3. Proses Penghapusan
        squad_name = squad.name
        squad.delete()

        # 4. Return Success Response (Struktur Flat)
        return JsonResponse({
            'success': True,
            'message': f'Squad "{squad_name}" has been deleted.',
            'deleted_squad_id': squad_id
        })

    except Exception as e:
        # Log error ke terminal server untuk debugging jika ada crash tak terduga
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Gagal menghapus squad: {str(e)}'
        }, status=500)
    
@login_required
def select_squad_for_player(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    error_message = None
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
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

                if DreamSquadPlayer.objects.filter(squad=selected_squad, player=player).exists():
                    error_message = f'Pemain {player.name} sudah terdaftar di squad {selected_squad.name}.'

                elif current_squad_info.player_count >= MAX_PLAYERS:
                    error_message = f'Squad {selected_squad.name} sudah penuh (Maksimal {MAX_PLAYERS} pemain).'
                
                else:
                    DreamSquadPlayer.objects.create(
                        squad=selected_squad, 
                        player=player
                    )
                    
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

        if is_ajax and error_message:
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)

    for squad in squads:
        squad.is_full = squad.player_count >= MAX_PLAYERS
        squad.has_player = DreamSquadPlayer.objects.filter(squad=squad, player=player).exists()
    
    context = {
        'player': player,
        'squads': squads,
        'MAX_PLAYERS': MAX_PLAYERS,
        'error': error_message,
    }

    if is_ajax:
        html = render_to_string('partials/select_squad_modal_content.html', context, request=request)
        return JsonResponse({'html': html})

    return render(request, 'select_squad.html', context)
    

@login_required
def player_detail(request, player_id):
    """Menampilkan statistik detail untuk pemain tertentu."""
    player = get_object_or_404(Player.objects.select_related('club'), id=player_id)
    context = {
        'player': player,
    }
    return render(request, 'player_detail.html', context) 

@require_http_methods(["GET"])
def api_player_detail(request, player_id):
    """
    API Detail Pemain - Mengikuti pola stabil untuk Flutter.
    Menghindari return HTML jika ID tidak ditemukan atau terjadi error server.
    """
    try:
        # 1. Ambil Data Pemain (Cek manual agar return JSON 404, bukan HTML 404)
        try:
            player = Player.objects.select_related('club').get(id=player_id)
        except Player.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Pemain dengan ID {player_id} tidak ditemukan.'
            }, status=404)

        # 2. Susun Data (Pastikan semua nilai memiliki default agar tidak 'Null' di Flutter)
        # Struktur dibuat flat di level utama, lalu dikelompokkan sesuai kategori
        response_data = {
            'success': True,
            'id': player.id,
            'name': player.name,
            'image_url': player.image.url if hasattr(player, 'image') and player.image else None,
            'position_display': player.get_position_display() if hasattr(player, 'get_position_display') else player.position,
            'position_raw': player.position,
            'club_name': player.club.name if player.club else "Free Agent",
            'nation': getattr(player, 'nation', 'N/A') or 'N/A',
            'league': getattr(player, 'league', 'N/A') or 'N/A',
            'season': getattr(player, 'season', 'N/A') or 'N/A',
            'age': getattr(player, 'age', 0) or 0,
            'born': str(getattr(player, 'born', '-')) if getattr(player, 'born', None) else '-',

            # --- Statistik Kelompok (Dikirim sebagai objek/map) ---
            'attacking': {
                'goals': getattr(player, 'goals', 0) or 0,
                'assists': getattr(player, 'assists', 0) or 0,
                'xg': float(getattr(player, 'xg', 0.0) or 0.0),
                'xag': float(getattr(player, 'xag', 0.0) or 0.0),
            },

            'passing': {
                'pass_accuracy': float(getattr(player, 'pass_accuracy', 0.0) or 0.0),
                'passes_completed': getattr(player, 'passes_completed', 0) or 0,
                'passes_attempted': getattr(player, 'passes_attempted', 0) or 0,
                'prgc': getattr(player, 'prgc', 0) or 0,
                'prgp': getattr(player, 'prgp', 0) or 0,
                'prgr': getattr(player, 'prgr', 0) or 0,
            },

            'defensive': {
                'tackles': getattr(player, 'tackles', 0) or 0,
                'tackles_won': getattr(player, 'tackles_won', 0) or 0,
                'challenges_won': getattr(player, 'challenges_won', 0) or 0,
                'challenges_attempted': getattr(player, 'challenges_attempted', 0) or 0,
                'blocks': getattr(player, 'blocks', 0) or 0,
                'clearances': getattr(player, 'clearances', 0) or 0,
            },

            'advanced': {
                'npxg': float(getattr(player, 'npxg', 0.0) or 0.0),
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Log error ke terminal server agar Anda bisa melihat apa yang salah
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Gagal mengambil detail pemain: {str(e)}'
        }, status=500)