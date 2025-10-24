from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Count


from PlayerClub_Data.forms import ClubForm, PlayerForm
from PlayerClub_Data.models import Club, Player
from forum.models import Post, Comment
from users.models import ADMIN_USERNAMES, Profile


def _is_admin(user):
    return hasattr(user, "profile") and user.profile.role == "admin"


@login_required
@user_passes_test(_is_admin)
def dashboard(request):
    users = (
        User.objects.select_related("profile")
        .filter(profile__isnull=False)
        .order_by("username")
    )
    clubs = Club.objects.all().order_by("name")
    players = Player.objects.select_related("club").order_by("name")

    posts_recent = (
        Post.objects.select_related("author")
        .annotate(comment_count=Count("comments", distinct=True), like_count=Count("likes", distinct=True))
        .order_by("-created_at")[:8]
    )
    comments_recent = (
        Comment.objects.select_related("user", "post")
        .annotate(like_count=Count("likes", distinct=True))
        .order_by("-created_at")[:8]
    )

    stats = {
        "total_users": users.count(),
        "blocked_users": users.filter(profile__is_blocked=True).count(),
        "flagged_users": users.filter(profile__is_flagged=True).count(),
        "total_posts": Post.objects.count(),
        "total_comments": Comment.objects.count(),
    }

    context = {
        "users": users,
        "role_choices": Profile.ROLE_CHOICES,
        "clubs": clubs,
        "players": players,
        "locked_usernames": ADMIN_USERNAMES,
        "posts_recent": posts_recent,
        "comments_recent": comments_recent,
        "stats": stats,
    }
    return render(request, "adminpanel/dashboard.html", context)


@login_required
@user_passes_test(_is_admin)
@require_POST
def update_user_role(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    new_role = (request.POST.get("role") or "").strip()
    valid_roles = {choice[0] for choice in Profile.ROLE_CHOICES}

    if new_role not in valid_roles:
        messages.error(request, "Invalid role selected.")
        return redirect("adminpanel:dashboard")

    if profile.user.username in ADMIN_USERNAMES and new_role != "admin":
        messages.warning(request, "This account is locked as admin and cannot be downgraded.")
        return redirect("adminpanel:dashboard")

    if profile.role == new_role:
        messages.info(request, "Role is already up to date.")
        return redirect("adminpanel:dashboard")

    profile.role = new_role
    profile.save(update_fields=["role"])
    messages.success(request, f"Role for {profile.user.username} updated to {profile.get_role_display()}.")
    return redirect("adminpanel:dashboard")


@login_required
@user_passes_test(_is_admin)
def club_create(request):
    if request.method == "POST":
        form = ClubForm(request.POST)
        if form.is_valid():
            club = form.save()
            messages.success(request, f"Club '{club.name}' created.")
            return redirect("adminpanel:dashboard")
    else:
        form = ClubForm()

    return render(
        request,
        "adminpanel/club_form.html",
        {
            "form": form,
            "title": "Add Club",
            "submit_label": "Create Club",
            "cancel_url": reverse("adminpanel:dashboard"),
        },
    )


@login_required
@user_passes_test(_is_admin)
def club_update(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.method == "POST":
        form = ClubForm(request.POST, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, f"Club '{club.name}' updated.")
            return redirect("adminpanel:dashboard")
    else:
        form = ClubForm(instance=club)

    return render(
        request,
        "adminpanel/club_form.html",
        {
            "form": form,
            "title": f"Edit Club: {club.name}",
            "submit_label": "Update Club",
            "cancel_url": reverse("adminpanel:dashboard"),
        },
    )


@login_required
@user_passes_test(_is_admin)
def club_delete(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.method == "POST":
        name = club.name
        club.delete()
        messages.success(request, f"Club '{name}' deleted.")
        return redirect("adminpanel:dashboard")

    return render(
        request,
        "adminpanel/confirm_delete.html",
        {
            "object_name": club.name,
            "entity_label": "club",
            "cancel_url": reverse("adminpanel:dashboard"),
        },
    )


@login_required
@user_passes_test(_is_admin)
def player_create(request):
    if request.method == "POST":
        form = PlayerForm(request.POST)
        if form.is_valid():
            player = form.save()
            messages.success(request, f"Player '{player.name}' created.")
            return redirect("adminpanel:dashboard")
    else:
        form = PlayerForm()

    return render(
        request,
        "adminpanel/player_form.html",
        {
            "form": form,
            "title": "Add Player",
            "submit_label": "Create Player",
            "cancel_url": reverse("adminpanel:dashboard"),
        },
    )


@login_required
@user_passes_test(_is_admin)
def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == "POST":
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f"Player '{player.name}' updated.")
            return redirect("adminpanel:dashboard")
    else:
        form = PlayerForm(instance=player)

    return render(
        request,
        "adminpanel/player_form.html",
        {
            "form": form,
            "title": f"Edit Player: {player.name}",
            "submit_label": "Update Player",
            "cancel_url": reverse("adminpanel:dashboard"),
        },
    )


@login_required
@user_passes_test(_is_admin)
def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == "POST":
        name = player.name
        player.delete()
        messages.success(request, f"Player '{name}' deleted.")
        return redirect("adminpanel:dashboard")

    return render(
        request,
        "adminpanel/confirm_delete.html",
        {
            "object_name": player.name,
            "entity_label": "player",
            "cancel_url": reverse("adminpanel:dashboard"),
        },
    )
