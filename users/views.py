from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import Profile
from PlayerClub_Data.models import Club
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
import json

def login_user(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  
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

    paginator = Paginator(qs, 12)  
    page_obj = paginator.get_page(request.GET.get('page'))
    active_filters = sum(1 for value in (q, league, position) if value)

    context = {
        'page_obj': page_obj,
        'q': q,
        'league': league,
        'position': position,
        'LEAGUE_CHOICES': Profile.LEAGUE_CHOICES,
        'POSITION_CHOICES': Profile.POSITION_CHOICES,
        'active_filters': active_filters,
        'results_count': paginator.count,
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
            "role": p.role or "",
            "bio": (p.bio or "").strip(),
            "member_since": p.user.date_joined.strftime("%B %Y") if p.user.date_joined else "",
            "instagram_url": p.instagram_url,
            "x_url": p.x_url,
            "website_url": p.website_url,
        })

    return JsonResponse({"status": True, "results": results}, status=200)

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

def serialize_profile(profile, include_email=False):
    user = profile.user
    return {
        "username": user.username,
        "name": (user.get_full_name() or "").strip(),
        "email": user.email if include_email else "",
        "favorite_team": profile.favorite_team.name if profile.favorite_team else None,
        "favorite_team_id": profile.favorite_team.id if profile.favorite_team else None,
        "favorite_league": profile.get_favorite_league_display() if profile.favorite_league else None,
        "preferred_position": profile.get_preferred_position_display() if profile.preferred_position else None,
        "avatar": profile.profile_picture,
        "role": profile.role or "",
        "bio": (profile.bio or "").strip(),
        "member_since": user.date_joined.isoformat() if user.date_joined else "",
        "instagram_url": profile.instagram_url,
        "x_url": profile.x_url,
        "website_url": profile.website_url,
        "is_blocked": profile.is_blocked,
        "is_flagged": profile.is_flagged,
    }

@csrf_exempt
def profile_me_api(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": False, "message": "Authentication required."},
            status=401,
        )

    profile, _ = Profile.objects.select_related('user', 'favorite_team').get_or_create(
        user=request.user
    )

    if request.method == "GET":
        data = serialize_profile(profile, include_email=True)
        return JsonResponse({"status": True, "data": data}, status=200)

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": False, "message": "Invalid JSON payload."},
                status=400,
            )

        team_id = payload.get("favorite_team_id", None)
        team_name = payload.get("favorite_team", None)

        if team_id is not None:
            try:
                profile.favorite_team = Club.objects.get(pk=team_id)
            except Club.DoesNotExist:
                profile.favorite_team = None

        elif team_name is not None:
            team_name_str = (team_name or "").strip()
            if team_name_str == "":
                profile.favorite_team = None
            else:
                club_obj = Club.objects.filter(name__iexact=team_name_str).first()
                profile.favorite_team = club_obj  

        editable_fields = [
            "bio",
            "profile_picture",
            "favorite_league",
            "preferred_position",
            "instagram_url",
            "x_url",
            "website_url",
        ]

        for field in editable_fields:
            if field in payload:
                value = payload.get(field)
                setattr(profile, field, value if value != "" else None)

        profile.save()

        return JsonResponse(
            {"status": True, "message": "Profile updated successfully."},
            status=200,
        )

    return JsonResponse(
        {"status": False, "message": "Method not allowed."},
        status=405,
    )



@login_required
def list_users_api(request):
    try:
        limit = int(request.GET.get("limit", 50))
    except ValueError:
        limit = 50

    limit = max(1, min(limit, 200))  

    qs = Profile.objects.select_related('user', 'favorite_team') \
                        .order_by('user__username')[:limit]

    results = [serialize_profile(p) for p in qs]

    return JsonResponse(
        {"status": True, "count": len(results), "results": results},
        status=200,
    )

def profile_detail_api(request, username):
    profile = get_object_or_404(
        Profile.objects.select_related('user', 'favorite_team'),
        user__username__iexact=username,
    )

    include_email = (request.user == profile.user) 
    data = serialize_profile(profile, include_email=include_email)

    return JsonResponse(
        {"status": True, "data": data},
        status=200,
    )

@require_GET
def image_proxy(request):
    url = (request.GET.get("url") or "").strip()
    if not url:
        return JsonResponse({"status": False, "message": "Missing url"}, status=400)

    if not (url.startswith("http://") or url.startswith("https://")):
        return JsonResponse(
            {"status": False, "message": "Invalid scheme"},
            status=400
        )

    try:
        r = requests.get(url, timeout=10, stream=True)
        content_type = r.headers.get("Content-Type", "image/png")

        response = HttpResponse(r.content, content_type=content_type)
        response["Access-Control-Allow-Origin"] = "*"   # WAJIB buat Flutter Web
        response["Cache-Control"] = "public, max-age=86400"
        return response

    except requests.RequestException:
        return JsonResponse(
            {"status": False, "message": "Failed to fetch image"},
            status=502
        )

