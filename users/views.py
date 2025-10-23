from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import Profile
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme

def login_user(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Django otomatis buat session ID + cookie
            messages.success(request, f"Welcome back, {username}!")
            return redirect('main:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('users:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('users:register')

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)

        messages.success(request, "Registration successful. Please log in.")
        return redirect('users:login')

    return render(request, 'register.html')

def logout_user(request):
    logout(request)  
    messages.info(request, "You have been logged out.")
    return redirect('main:home')

@login_required
def search_users(request):
    q = (request.GET.get('q') or '').strip()
    league = (request.GET.get('league') or '').strip()
    position = (request.GET.get('position') or '').strip()

    qs = Profile.objects.select_related('user', 'favorite_team')

    if q:
        qs = qs.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(bio__icontains=q) |
            Q(favorite_team__name__icontains=q)
        )

    if league:
        qs = qs.filter(favorite_league=league)

    if position:
        qs = qs.filter(preferred_position=position)

    qs = qs.order_by('user__username')

    paginator = Paginator(qs, 12)  # 12 kartu per halaman
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'q': q,
        'league': league,
        'position': position,
        'LEAGUE_CHOICES': Profile.LEAGUE_CHOICES,
        'POSITION_CHOICES': Profile.POSITION_CHOICES,
    }
    return render(request, 'search.html', context)

@login_required
def search_users_api(request):
    q = (request.GET.get('q') or '').strip()
    league = (request.GET.get('league') or '').strip()
    position = (request.GET.get('position') or '').strip()

    qs = Profile.objects.select_related('user', 'favorite_team')

    if q:
        qs = qs.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(bio__icontains=q) |
            Q(favorite_team__name__icontains=q)
        )

    if league:
        qs = qs.filter(favorite_league=league)

    if position:
        qs = qs.filter(preferred_position=position)

    qs = qs.order_by('user__username')[:50]  

    results = []
    for p in qs:
        results.append({
            "username": p.user.username,
            "name": (p.user.get_full_name() or "").strip(),
            "favorite_team": p.favorite_team.name if p.favorite_team else None,
            "favorite_league": p.get_favorite_league_display() if p.favorite_league else None,
            "preferred_position": p.get_preferred_position_display() if p.preferred_position else None,
            "avatar": p.profile_picture,
        })

    return JsonResponse({"results": results})

@login_required
def view_profile(request, username):
    profile = get_object_or_404(
        Profile.objects.select_related('user', 'favorite_team'),
        user__username__iexact=username
    )
    is_owner = request.user == profile.user

    form = None
    if is_owner:
        if request.method == "POST":
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return redirect('users:profile', username=username)
        else:
            form = ProfileForm(instance=profile)

    return render(request, "profile.html", {
        "profile": profile,
        "is_owner": is_owner,
        "form": form,
    })

@login_required
def toggle_block_user(request, username):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "Unauthorized.")
        return redirect('users:search_users')

    target = get_object_or_404(Profile, user__username=username)
    target.is_blocked = not target.is_blocked
    target.save()
    messages.success(request, f"User '{username}' has been {'blocked' if target.is_blocked else 'unblocked'}.")
    next_url = request.GET.get('next') or request.POST.get('next')
    allowed_hosts = {request.get_host()}
    allowed_hosts.update(settings.ALLOWED_HOSTS)
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=allowed_hosts):
        return redirect(next_url)
    return redirect('users:profile', username=username)


@login_required
def toggle_flag_user(request, username):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "Unauthorized.")
        return redirect('users:search_users')

    target = get_object_or_404(Profile, user__username=username)
    target.is_flagged = not target.is_flagged
    target.save()
    messages.success(request, f"User '{username}' flag status updated.")
    next_url = request.GET.get('next') or request.POST.get('next')
    allowed_hosts = {request.get_host()}
    allowed_hosts.update(settings.ALLOWED_HOSTS)
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=allowed_hosts):
        return redirect(next_url)
    return redirect('users:profile', username=username)
