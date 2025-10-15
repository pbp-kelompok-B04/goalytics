from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from .forms import ProfileForm

# --------- PAGES ---------
def login_page(request):
    get_token(request)  # siapkan CSRF cookie
    if request.user.is_authenticated:
        return redirect("goalytics_app:profile.me")
    return render(request, "auth/login.html")

def register_page(request):
    get_token(request)
    if request.user.is_authenticated:
        return redirect("goalytics_app:profile.me")
    return render(request, "auth/register.html")

@login_required
def me_page(request):
    get_token(request)
    return render(request, "profile/me.html", {"profile": request.user.profile})

@login_required
def edit_page(request):
    get_token(request)
    return render(request, "profile/edit.html", {"profile": request.user.profile})

# --------- API (AJAX JSON) ---------
@require_POST
def api_register(request):
    form = UserCreationForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True, "message": "Akun dibuat. Silakan login."})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@require_POST
def api_login(request):
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
        login(request, form.get_user())
        return JsonResponse({"ok": True, "message": "Login berhasil"})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@require_POST
def api_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({"ok": True, "message": "Logout berhasil"})

@login_required
def api_profile_me(request):
    p = request.user.profile
    return JsonResponse({
        "ok": True,
        "data": {
            "username": request.user.username,
            "email": request.user.email,
            "preferred_league": p.preferred_league,
            "favorite_club": p.favorite_club,
            "display_mode": p.display_mode,
            "bio": p.bio,
        },
    })

@require_POST
@login_required
def api_profile_update(request):
    form = ProfileForm(request.POST, instance=request.user.profile)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True, "message": "Profil berhasil diperbarui"})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
