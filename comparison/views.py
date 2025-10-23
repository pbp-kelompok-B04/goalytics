from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from PlayerClub_Data.models import Player, Club  

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

def compare_players_api(request):
    """API untuk compare players - SESUAIKAN DENGAN MODEL BARU"""
    try:
        player1_id = request.GET.get('player1_id')
        player2_id = request.GET.get('player2_id')
        
        player1 = Player.objects.get(id=player1_id)
        player2 = Player.objects.get(id=player2_id)
        
        # Stats yang akan ditampilkan di comparison
        context = {
            'player1': player1,
            'player2': player2,
            # Max values untuk progress bars
            'max_goals': max(player1.goals or 0, player2.goals or 0) or 1,
            'max_assists': max(player1.assists or 0, player2.assists or 0) or 1,
            'max_xg': max(player1.xg or 0, player2.xg or 0) or 1,
            'max_pass_accuracy': max(player1.pass_accuracy or 0, player2.pass_accuracy or 0) or 1,
            'max_tackles': max(player1.tackles or 0, player2.tackles or 0) or 1,
            'max_progressive_passes': max(player1.Progressive_Passes or 0, player2.Progressive_Passes or 0) or 1,
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