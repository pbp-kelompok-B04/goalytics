from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TransferRumourForm
from .models import TransferRumour


def _get_role(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


def _is_admin(user) -> bool:
    return _get_role(user) == "admin"


def _can_publish(user) -> bool:
    return _get_role(user) in {"admin", "analyst"}


def _can_manage_rumour(user, rumour) -> bool:
    if not _can_publish(user):
        return False
    if _is_admin(user):
        return True
    return rumour.author_id == user.id


def rumour_list(request):
    rumours_qs = (
        TransferRumour.objects.select_related("author", "author__profile")
        .all()
    )
    rumours = list(rumours_qs)
    manageable_ids = []
    if request.user.is_authenticated:
        manageable_ids = [
            rumour.id for rumour in rumours if _can_manage_rumour(request.user, rumour)
        ]

    context = {
        "rumours": rumours,
        "can_publish": request.user.is_authenticated and _can_publish(request.user),
        "is_admin": request.user.is_authenticated and _is_admin(request.user),
        "manageable_ids": manageable_ids,
    }
    return render(request, "transfer_rumour/list.html", context)


def rumour_detail(request, slug):
    rumour = get_object_or_404(
        TransferRumour.objects.select_related("author", "author__profile"),
        slug=slug,
    )
    can_manage = request.user.is_authenticated and _can_manage_rumour(request.user, rumour)
    return render(
        request,
        "transfer_rumour/detail.html",
        {
            "rumour": rumour,
            "can_manage": can_manage,
        },
    )


@login_required
def rumour_create(request):
    if not _can_publish(request.user):
        messages.error(request, "Hanya admin atau analyst yang dapat membuat rumour baru.")
        return redirect("transfer_rumour:list")

    if request.method == "POST":
        form = TransferRumourForm(request.POST)
        if form.is_valid():
            rumour = form.save(commit=False)
            rumour.author = request.user
            rumour.save()
            messages.success(request, "Rumour transfer berhasil dibuat.")
            return redirect("transfer_rumour:detail", slug=rumour.slug)
    else:
        form = TransferRumourForm()

    return render(
        request,
        "transfer_rumour/form.html",
        {
            "form": form,
            "form_title": "Tulis Transfer Rumour",
            "form_description": "Bagikan insight perpindahan pemain versi Anda.",
            "submit_label": "Simpan Rumour",
        },
    )


@login_required
def rumour_update(request, slug):
    rumour = get_object_or_404(TransferRumour, slug=slug)
    if not _can_manage_rumour(request.user, rumour):
        messages.error(request, "Anda tidak memiliki izin untuk mengubah rumour ini.")
        return redirect("transfer_rumour:detail", slug=rumour.slug)

    if request.method == "POST":
        form = TransferRumourForm(request.POST, instance=rumour)
        if form.is_valid():
            form.save()
            messages.success(request, "Rumour berhasil diperbarui.")
            return redirect("transfer_rumour:detail", slug=rumour.slug)
    else:
        form = TransferRumourForm(instance=rumour)

    return render(
        request,
        "transfer_rumour/form.html",
        {
            "form": form,
            "form_title": "Edit Transfer Rumour",
            "form_description": "Perbarui detail rumour perpindahan pemain.",
            "submit_label": "Perbarui Rumour",
            "is_update": True,
        },
    )


@login_required
def rumour_delete(request, slug):
    rumour = get_object_or_404(TransferRumour, slug=slug)
    if not _can_manage_rumour(request.user, rumour):
        messages.error(request, "Anda tidak memiliki izin untuk menghapus rumour ini.")
        return redirect("transfer_rumour:detail", slug=rumour.slug)

    if request.method == "POST":
        rumour.delete()
        messages.success(request, "Rumour berhasil dihapus.")
        return redirect("transfer_rumour:list")

    return render(
        request,
        "transfer_rumour/confirm_delete.html",
        {
            "rumour": rumour,
        },
    )
