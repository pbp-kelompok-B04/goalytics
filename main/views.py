from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from transfer_rumour.models import TransferRumour
from PlayerClub_Data.models import Player
from forum.models import Post

from django.views.decorators.csrf import ensure_csrf_cookie

def home(request):
    rumour_highlights = TransferRumour.objects.order_by('-created_at')[:2]
    player_samples = Player.objects.select_related('club').order_by('name')[:2]
    forum_snippets = Post.objects.select_related('author').order_by('-created_at')[:2]

    context = {
        'cta_url': 'main:dashboard' if request.user.is_authenticated else 'users:login',
        'cta_label': 'Go to Dashboard' if request.user.is_authenticated else 'Login to Goalytics',
        'rumour_highlights': rumour_highlights,
        'player_samples': player_samples,
        'forum_snippets': forum_snippets,
    }
    return render(request, 'home.html', context)

@login_required
def dashboard(request):
    user = request.user
    context = {
        'username': user.username,
        'email': user.email,
    }
    return render(request, 'dashboard.html', context)
