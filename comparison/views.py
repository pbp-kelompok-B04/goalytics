from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Max
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from PlayerClub_Data.models import Player, Club  
import json
import traceback
from django.utils.safestring import mark_safe
from .models import SavedComparison

def comparison_view(request):
    return render(request, 'comparison/comparison.html')

def player_search_api(request):
    """API untuk search players"""
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'players': []})
        
        players = Player.objects.filter(
            Q(name__icontains=query)
        )[:10]
        
        players_data = []
        for player in players:
            players_data.append({
                'id': player.id,
                'name': player.name,
                'club': player.club.name if player.club else 'No Club',
                'position': player.position or 'Unknown'
            })
        
        return JsonResponse({'players': players_data})
        
    except Exception as e:
        return JsonResponse({'players': []})

def get_position_stats(player):
    """Get position-specific statistics for a player"""
    position = player.position
    stats = {}
    
    if position == 'GK':
        stats = {
            'goals': player.goals or 0,
            'assists': player.assists or 0,
            'saves': player.saves or 0,
            'save_percentage': player.save_percentage or 0,
            'clean_sheets': player.clean_sheets or 0,
            'clean_sheet_percentage': player.clean_sheet_percentage or 0,
        }
    elif position == 'DF':
        stats = {
            'goals': player.goals or 0,
            'assists': player.assists or 0,
            'tackles': player.tackles or 0,
            'tackles_won': player.tackles_won or 0,
            'challenges_won': player.challenges_won or 0,
            'challenges_attempted': player.challenges_attempted or 0,
            'blocks': player.blocks or 0,
            'clearances': player.clearances or 0,
        }
    elif position == 'MF':
        stats = {
            'goals': player.goals or 0,
            'assists': player.assists or 0,
            'Progressive_Carries': player.Progressive_Carries or 0,
            'Progressive_Passes': player.Progressive_Passes or 0,
            'Progressive_Receptions': player.Progressive_Receptions or 0,
            'passes_completed': player.passes_completed or 0,
            'passes_attempted': player.passes_attempted or 0,
            'pass_accuracy': player.pass_accuracy or 0,
            'xag': player.xag or 0,
        }
    elif position == 'FW':
        stats = {
            'goals': player.goals or 0,
            'assists': player.assists or 0,
            'xg': player.xg or 0,
            'npxg': player.npxg or 0,
            'xag': player.xag or 0,
        }
    else:
        # Default stats untuk posisi unknown
        stats = {
            'goals': player.goals or 0,
            'assists': player.assists or 0,
            'xg': player.xg or 0,
        }
    
    return stats

def get_max_values():
    """Get maximum values for all relevant stats from database"""
    return {
        'goals': Player.objects.aggregate(Max('goals'))['goals__max'] or 1,
        'assists': Player.objects.aggregate(Max('assists'))['assists__max'] or 1,
        'saves': Player.objects.aggregate(Max('saves'))['saves__max'] or 1,
        'save_percentage': Player.objects.aggregate(Max('save_percentage'))['save_percentage__max'] or 100,
        'clean_sheets': Player.objects.aggregate(Max('clean_sheets'))['clean_sheets__max'] or 1,
        'clean_sheet_percentage': Player.objects.aggregate(Max('clean_sheet_percentage'))['clean_sheet_percentage__max'] or 100,
        'tackles': Player.objects.aggregate(Max('tackles'))['tackles__max'] or 1,
        'tackles_won': Player.objects.aggregate(Max('tackles_won'))['tackles_won__max'] or 1,
        'challenges_won': Player.objects.aggregate(Max('challenges_won'))['challenges_won__max'] or 1,
        'challenges_attempted': Player.objects.aggregate(Max('challenges_attempted'))['challenges_attempted__max'] or 1,
        'blocks': Player.objects.aggregate(Max('blocks'))['blocks__max'] or 1,
        'clearances': Player.objects.aggregate(Max('clearances'))['clearances__max'] or 1,
        'Progressive_Carries': Player.objects.aggregate(Max('Progressive_Carries'))['Progressive_Carries__max'] or 1,
        'Progressive_Passes': Player.objects.aggregate(Max('Progressive_Passes'))['Progressive_Passes__max'] or 1,
        'Progressive_Receptions': Player.objects.aggregate(Max('Progressive_Receptions'))['Progressive_Receptions__max'] or 1,
        'passes_completed': Player.objects.aggregate(Max('passes_completed'))['passes_completed__max'] or 1,
        'passes_attempted': Player.objects.aggregate(Max('passes_attempted'))['passes_attempted__max'] or 1,
        'pass_accuracy': Player.objects.aggregate(Max('pass_accuracy'))['pass_accuracy__max'] or 100,
        'xag': Player.objects.aggregate(Max('xag'))['xag__max'] or 1,
        'xg': Player.objects.aggregate(Max('xg'))['xg__max'] or 1,
        'npxg': Player.objects.aggregate(Max('npxg'))['npxg__max'] or 1,
    }

def compare_players_api(request):
    """API untuk compare players - SESUAIKAN DENGAN MODEL BARU"""
    try:
        player1_id = request.GET.get('player1_id')
        player2_id = request.GET.get('player2_id')
        
        player1 = Player.objects.get(id=player1_id)
        player2 = Player.objects.get(id=player2_id)
        
        # Stats yang akan ditampilkan di comparison
        player1_stats = {
            'goals': player1.goals or 0,
            'assists': player1.assists or 0,
            'xg': player1.xg or 0,
            'npxg': player1.npxg or 0,
            'xag': player1.xag or 0,
            'Progressive_Carries': player1.Progressive_Carries or 0,
            'Progressive_Passes': player1.Progressive_Passes or 0,
            'Progressive_Receptions': player1.Progressive_Receptions or 0,
            'passes_completed': player1.passes_completed or 0,
            'passes_attempted': player1.passes_attempted or 0,
            'pass_accuracy': player1.pass_accuracy or 0,
            'tackles': player1.tackles or 0,
            'tackles_won': player1.tackles_won or 0,
            'challenges_won': player1.challenges_won or 0,
            'challenges_attempted': player1.challenges_attempted or 0,
            'blocks': player1.blocks or 0,
            'clearances': player1.clearances or 0,
            'saves': player1.saves or 0,
            'save_percentage': player1.save_percentage or 0,
            'clean_sheets': player1.clean_sheets or 0,
            'clean_sheet_percentage': player1.clean_sheet_percentage or 0,
        }
        
        player2_stats = {
            'goals': player2.goals or 0,
            'assists': player2.assists or 0,
            'xg': player2.xg or 0,
            'npxg': player2.npxg or 0,
            'xag': player2.xag or 0,
            'Progressive_Carries': player2.Progressive_Carries or 0,
            'Progressive_Passes': player2.Progressive_Passes or 0,
            'Progressive_Receptions': player2.Progressive_Receptions or 0,
            'passes_completed': player2.passes_completed or 0,
            'passes_attempted': player2.passes_attempted or 0,
            'pass_accuracy': player2.pass_accuracy or 0,
            'tackles': player2.tackles or 0,
            'tackles_won': player2.tackles_won or 0,
            'challenges_won': player2.challenges_won or 0,
            'challenges_attempted': player2.challenges_attempted or 0,
            'blocks': player2.blocks or 0,
            'clearances': player2.clearances or 0,
            'saves': player2.saves or 0,
            'save_percentage': player2.save_percentage or 0,
            'clean_sheets': player2.clean_sheets or 0,
            'clean_sheet_percentage': player2.clean_sheet_percentage or 0,
        }
        
        # Calculate max values untuk progress bars
        max_values = {
            'goals': max(player1_stats['goals'], player2_stats['goals']) or 1,
            'assists': max(player1_stats['assists'], player2_stats['assists']) or 1,
            'xg': max(player1_stats['xg'], player2_stats['xg']) or 1,
            'npxg': max(player1_stats['npxg'], player2_stats['npxg']) or 1,
            'xag': max(player1_stats['xag'], player2_stats['xag']) or 1,
            'Progressive_Carries': max(player1_stats['Progressive_Carries'], player2_stats['Progressive_Carries']) or 1,
            'Progressive_Passes': max(player1_stats['Progressive_Passes'], player2_stats['Progressive_Passes']) or 1,
            'Progressive_Receptions': max(player1_stats['Progressive_Receptions'], player2_stats['Progressive_Receptions']) or 1,
            'passes_completed': max(player1_stats['passes_completed'], player2_stats['passes_completed']) or 1,
            'passes_attempted': max(player1_stats['passes_attempted'], player2_stats['passes_attempted']) or 1,
            'pass_accuracy': max(player1_stats['pass_accuracy'], player2_stats['pass_accuracy']) or 1,
            'tackles': max(player1_stats['tackles'], player2_stats['tackles']) or 1,
            'tackles_won': max(player1_stats['tackles_won'], player2_stats['tackles_won']) or 1,
            'challenges_won': max(player1_stats['challenges_won'], player2_stats['challenges_won']) or 1,
            'challenges_attempted': max(player1_stats['challenges_attempted'], player2_stats['challenges_attempted']) or 1,
            'blocks': max(player1_stats['blocks'], player2_stats['blocks']) or 1,
            'clearances': max(player1_stats['clearances'], player2_stats['clearances']) or 1,
            'saves': max(player1_stats['saves'] or 0, player2_stats['saves'] or 0) or 1,
            'save_percentage': max(player1_stats['save_percentage'] or 0, player2_stats['save_percentage'] or 0) or 1,
            'clean_sheets': max(player1_stats['clean_sheets'] or 0, player2_stats['clean_sheets'] or 0) or 1,
            'clean_sheet_percentage': max(player1_stats['clean_sheet_percentage'] or 0, player2_stats['clean_sheet_percentage'] or 0) or 1,
        }
        
        # Radar chart data (hanya untuk players dengan position sama)
        same_position = player1.position == player2.position
        radar_labels = []
        radar_data1 = []
        radar_data2 = []
        radar_max = []
        
        if same_position:
            if player1.position == 'FW':
                radar_labels = ['goals', 'assists', 'xg', 'npxg', 'xag']
                radar_data1 = [player1_stats['goals'], player1_stats['assists'], player1_stats['xg'], player1_stats['npxg'], player1_stats['xag']]
                radar_data2 = [player2_stats['goals'], player2_stats['assists'], player2_stats['xg'], player2_stats['npxg'], player2_stats['xag']]
                radar_max = [max_values['goals'], max_values['assists'], max_values['xg'], max_values['npxg'], max_values['xag']]
            elif player1.position == 'MF':
                radar_labels = ['goals', 'assists', 'Progressive_Passes', 'pass_accuracy', 'xag']
                radar_data1 = [player1_stats['goals'], player1_stats['assists'], player1_stats['Progressive_Passes'], player1_stats['pass_accuracy'], player1_stats['xag']]
                radar_data2 = [player2_stats['goals'], player2_stats['assists'], player2_stats['Progressive_Passes'], player2_stats['pass_accuracy'], player2_stats['xag']]
                radar_max = [max_values['goals'], max_values['assists'], max_values['Progressive_Passes'], max_values['pass_accuracy'], max_values['xag']]
            elif player1.position == 'DF':
                radar_labels = ['tackles', 'tackles_won', 'blocks', 'clearances', 'challenges_won']
                radar_data1 = [player1_stats['tackles'], player1_stats['tackles_won'], player1_stats['blocks'], player1_stats['clearances'], player1_stats['challenges_won']]
                radar_data2 = [player2_stats['tackles'], player2_stats['tackles_won'], player2_stats['blocks'], player2_stats['clearances'], player2_stats['challenges_won']]
                radar_max = [max_values['tackles'], max_values['tackles_won'], max_values['blocks'], max_values['clearances'], max_values['challenges_won']]
            elif player1.position == 'GK':
                radar_labels = ['saves', 'save_percentage', 'clean_sheets', 'clean_sheet_percentage']
                radar_data1 = [player1_stats['saves'], player1_stats['save_percentage'], player1_stats['clean_sheets'], player1_stats['clean_sheet_percentage']]
                radar_data2 = [player2_stats['saves'], player2_stats['save_percentage'], player2_stats['clean_sheets'], player2_stats['clean_sheet_percentage']]
                radar_max = [max_values['saves'], max_values['save_percentage'], max_values['clean_sheets'], max_values['clean_sheet_percentage']]
        
        context = {
            'player1': player1,
            'player2': player2,
            'player1_stats': player1_stats,
            'player2_stats': player2_stats,
            'max_values': max_values,
            'same_position': same_position,
            'radar_labels': json.dumps(radar_labels),
            'radar_data1': json.dumps(radar_data1),
            'radar_data2': json.dumps(radar_data2),
            'radar_max': json.dumps(radar_max),
        }
        
        html = render_to_string('comparison/comparison_results.html', context)
        
        return JsonResponse({
            'success': True,
            'html': html
        })
        
    except Player.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Player not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Server error'
        }, status=500)

# Admin functions
def is_admin(user):
    """Check if user is admin"""
    try:
        return user.profile.role == 'admin'
    except:
        return False

@login_required
def create_player(request):
    """Create new player (admin only)"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Admin access required'}, status=403)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            position = request.POST.get('position')
            club_name = request.POST.get('club')
            
            # Get or create club
            club = None
            if club_name:
                club, _ = Club.objects.get_or_create(name=club_name)
            
            # Create player dengan field yang sesuai
            player = Player.objects.create(
                name=name,
                position=position,
                club=club,
                # Field lainnya default 0
                goals=0,
                assists=0,
                xg=0,
                npxg=0,
                xag=0,
                Progressive_Carries=0,
                Progressive_Passes=0,
                Progressive_Receptions=0,
                passes_completed=0,
                passes_attempted=0,
                tackles=0,
                tackles_won=0,
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Player {player.name} created successfully!',
                'player_id': player.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required  
def delete_player(request, player_id):
    """Delete player (admin only)"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Admin access required'}, status=403)
    
    if request.method == 'DELETE':
        try:
            player = Player.objects.get(id=player_id)
            player_name = player.name
            player.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'Player {player_name} deleted successfully!'
            })
            
        except Player.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Player not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
def save_comparison(request):
    """Save comparison to user's history"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            player1_id = data.get('player1_id')
            player2_id = data.get('player2_id')
            notes = data.get('notes', '')
            comparison_id = data.get('comparison_id')
            
            print(f"DEBUG: comparison_id={comparison_id}, player1={player1_id}, player2={player2_id}")
            
            # Mode EDIT dengan comparison_id
            if comparison_id:
                try:
                    # Cari comparison lama
                    old_comparison = SavedComparison.objects.get(
                        id=comparison_id,
                        user=request.user
                    )
                    
                    # Jika players berubah, kita perlu buat baru dan hapus yang lama
                    if (str(old_comparison.player1.id) != str(player1_id) or 
                        str(old_comparison.player2.id) != str(player2_id)):
                        
                        print(f"DEBUG: Players changed! Deleting old and creating new...")
                        
                        # Hapus comparison lama
                        old_comparison.delete()
                        
                        # Buat baru dengan players baru
                        player1 = Player.objects.get(id=player1_id)
                        player2 = Player.objects.get(id=player2_id)
                        
                        new_comparison = SavedComparison.objects.create(
                            user=request.user,
                            player1=player1,
                            player2=player2,
                            notes=notes
                        )
                        
                        return JsonResponse({
                            'success': True,
                            'message': 'Comparison updated with new players!',
                            'comparison_id': new_comparison.id,
                            'is_new': True
                        })
                    
                    # Jika players TIDAK berubah, cukup update notes
                    else:
                        old_comparison.notes = notes
                        old_comparison.save()
                        
                        return JsonResponse({
                            'success': True,
                            'message': 'Comparison notes updated!',
                            'comparison_id': old_comparison.id,
                            'is_new': False
                        })
                        
                except SavedComparison.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Comparison not found'}, status=404)
            
            # Mode CREATE baru (tanpa comparison_id)
            else:
                if not player1_id or not player2_id:
                    return JsonResponse({'success': False, 'error': 'Missing player IDs.'}, status=400)

                player1 = Player.objects.get(id=player1_id)
                player2 = Player.objects.get(id=player2_id)
                
                # Cek apakah sudah ada comparison yang sama
                existing = SavedComparison.objects.filter(
                    user=request.user,
                    player1=player1,
                    player2=player2
                ).first()
                
                if existing:
                    existing.notes = notes
                    existing.save()
                    message = 'Comparison notes updated!'
                    comparison_id = existing.id
                    is_new = False
                else:
                    comparison = SavedComparison.objects.create(
                        user=request.user,
                        player1=player1,
                        player2=player2,
                        notes=notes
                    )
                    message = 'Comparison saved successfully!'
                    comparison_id = comparison.id
                    is_new = True
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'comparison_id': comparison_id,
                    'is_new': is_new
                })
            
        except Exception as e:
            print(f"DEBUG Error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def comparison_view(request):
    """Render comparison page dengan parameter awal jika ada"""
    player1_id = request.GET.get('player1_id')
    player2_id = request.GET.get('player2_id')
    comparison_id = request.GET.get('comparison_id')
    notes = request.GET.get('notes', '')
    
    context = {
        'player1_id': player1_id,
        'player2_id': player2_id,
        'comparison_id': comparison_id,  # Kirim ke template
        'initial_notes': notes,  # Kirim notes awal
    }
    return render(request, 'comparison/comparison.html', context)

@login_required
def comparison_history(request):
    """Halaman untuk melihat history comparisons"""
    return render(request, 'comparison/comparison_history.html')

@login_required
def get_saved_comparisons(request):
    """API untuk get saved comparisons user"""
    comparisons = SavedComparison.objects.filter(user=request.user)
    
    comparisons_data = []
    for comp in comparisons:
        comparisons_data.append({
            'id': comp.id,
            'player1': {
                'id': comp.player1.id,
                'name': comp.player1.name,
                'club': comp.player1.club.name if comp.player1.club else 'No Club',
                'position': comp.player1.position
            },
            'player2': {
                'id': comp.player2.id,
                'name': comp.player2.name,
                'club': comp.player2.club.name if comp.player2.club else 'No Club', 
                'position': comp.player2.position
            },
            'created_at': comp.created_at.strftime('%d %b %Y, %H:%M'),
            'notes': comp.notes
        })
    
    return JsonResponse({'comparisons': comparisons_data})

@login_required
def delete_saved_comparison(request, comparison_id):
    """Delete saved comparison"""
    try:
        comparison = SavedComparison.objects.get(id=comparison_id, user=request.user)
        player1_name = comparison.player1.name
        player2_name = comparison.player2.name
        comparison.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Comparison {player1_name} vs {player2_name} deleted successfully!'
        })
    except SavedComparison.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Comparison not found'})

def get_player_by_id(request, player_id):
    """Get player by ID"""
    try:
        player = Player.objects.get(id=player_id)
        player_data = {
            'id': player.id,
            'name': player.name,
            'club': player.club.name if player.club else 'No Club',
            'position': player.position or 'Unknown'
        }
        return JsonResponse({'player': player_data})
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)

def compare_players_flutter(request):
    player1_id = request.GET.get('player1_id')
    player2_id = request.GET.get('player2_id')

    try:
        player1 = Player.objects.get(id=player1_id)
        player2 = Player.objects.get(id=player2_id)
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)

    data = {
        "player1": {
            "id": player1.id,
            "name": player1.name,
            "club": player1.club.name if player1.club else "No Club",
            "position": player1.position
        },
        "player2": {
            "id": player2.id,
            "name": player2.name,
            "club": player2.club.name if player2.club else "No Club",
            "position": player2.position
        },
        "stats1": {
            "goals": player1.goals or 0,
            "assists": player1.assists or 0,
            "xg": player1.xg or 0
        },
        "stats2": {
            "goals": player2.goals or 0,
            "assists": player2.assists or 0,
            "xg": player2.xg or 0
        }
    }

    return JsonResponse(data)

@login_required
def save_comparison_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            player1_id = data.get('player1_id')
            player2_id = data.get('player2_id')
            notes = data.get('notes', '')

            player1 = Player.objects.get(id=player1_id)
            player2 = Player.objects.get(id=player2_id)

            comparison, created = SavedComparison.objects.update_or_create(
                user=request.user,
                player1=player1,
                player2=player2,
                defaults={'notes': notes}
            )

            return JsonResponse({
                'success': True,
                'is_new': created,
                'comparison_id': comparison.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)

@login_required
def get_saved_comparisons_flutter(request):
    comparisons = SavedComparison.objects.filter(user=request.user)

    data = []
    for comp in comparisons:
        data.append({
            'id': comp.id,
            'player1': {
                'id': comp.player1.id,
                'name': comp.player1.name
            },
            'player2': {
                'id': comp.player2.id,
                'name': comp.player2.name
            },
            'notes': comp.notes,
            'created_at': comp.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({'data': data})

@login_required
def get_comparison_detail(request, comparison_id):
    try:
        comp = SavedComparison.objects.get(id=comparison_id, user=request.user)

        data = {
            'id': comp.id,
            'player1_id': comp.player1.id,
            'player2_id': comp.player2.id,
            'notes': comp.notes,
            'created_at': comp.created_at.strftime('%Y-%m-%d %H:%M')
        }

        return JsonResponse({'comparison': data})

    except SavedComparison.DoesNotExist:
        return JsonResponse({'error': 'Comparison not found'}, status=404)


