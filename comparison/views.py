from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Max
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from PlayerClub_Data.models import Player, Club  
import json
import traceback
from django.utils.safestring import mark_safe

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
    try:
        player1_id = request.GET.get('player1_id')
        player2_id = request.GET.get('player2_id')
        
        player1 = Player.objects.get(id=player1_id)
        player2 = Player.objects.get(id=player2_id)
        
        # Get position-specific stats
        player1_stats = get_position_stats(player1)
        player2_stats = get_position_stats(player2)
        
        # Get max values
        max_values = get_max_values()

        same_position = player1.position == player2.position

        # Radar chart data (only if same position)
        radar_labels = []
        radar_data1 = []
        radar_data2 = []
        radar_max = []

        if same_position:
            radar_labels = list(player1_stats.keys())
            radar_data1 = [player1_stats[k] or 0 for k in radar_labels]
            radar_data2 = [player2_stats.get(k, 0) or 0 for k in radar_labels]
            radar_max = [max_values.get(k, 1) or 1 for k in radar_labels]

        context = {
            'player1': player1,
            'player2': player2,
            'player1_stats': player1_stats,
            'player2_stats': player2_stats,
            'max_values': max_values,
            'same_position': same_position,
            'radar_labels': mark_safe(json.dumps(radar_labels)),
            'radar_data1': mark_safe(json.dumps(radar_data1)),
            'radar_data2': mark_safe(json.dumps(radar_data2)),
            'radar_max': mark_safe(json.dumps(radar_max)),
        }
        html = render_to_string('comparison/comparison_results.html', context)
        
        return JsonResponse({
            'success': True,
            'html': html,
            'radar_labels': radar_labels,
            'radar_data1': radar_data1,
            'radar_data2': radar_data2,
            'radar_max': radar_max,
            'player1_name': player1.name,
            'player2_name': player2.name,
        })
        
    except Player.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Player not found'
        }, status=404)
    except Exception as e:
        print("❌ Error comparing players:", str(e))
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
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