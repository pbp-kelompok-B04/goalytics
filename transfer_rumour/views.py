from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

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

    form = TransferRumourForm() if request.user.is_authenticated and _can_publish(request.user) else None

    context = {
        "rumours": rumours,
        "can_publish": request.user.is_authenticated and _can_publish(request.user),
        "is_admin": request.user.is_authenticated and _is_admin(request.user),
        "manageable_ids": manageable_ids,
        "form": form,
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
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "message": "Anda tidak memiliki izin untuk membuat rumour."},
                status=403,
            )
        messages.error(request, "Hanya admin atau analyst yang dapat membuat rumour baru.")
        return redirect("transfer_rumour:list")

    if request.method != "POST":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "message": "Method tidak diperbolehkan."},
                status=405,
            )
        return redirect("transfer_rumour:list")

    if request.method == "POST":
        form = TransferRumourForm(request.POST)
        if form.is_valid():
            rumour = form.save(commit=False)
            rumour.author = request.user
            rumour.save()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                card_html = render_to_string(
                    "transfer_rumour/partials/rumour_card.html",
                    {
                        "rumour": rumour,
                        "manageable_ids": [rumour.id],
                        "request": request,
                    },
                    request=request,
                )
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Rumour transfer berhasil dibuat.",
                        "card_html": card_html,
                        "detail_url": rumour.get_absolute_url() if hasattr(rumour, "get_absolute_url") else None,
                    }
                )
            messages.success(request, "Rumour transfer berhasil dibuat.")
            return redirect("transfer_rumour:detail", slug=rumour.slug)
        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                form_html = render_to_string(
                    "transfer_rumour/partials/form_fields.html",
                    {"form": form},
                    request=request,
                )
                return JsonResponse(
                    {"success": False, "form_html": form_html, "message": "Validasi gagal. Periksa isian Anda."},
                    status=400,
                )
    return redirect("transfer_rumour:list")


@login_required
def rumour_update(request, slug):
    rumour = get_object_or_404(TransferRumour, slug=slug)
    if not _can_manage_rumour(request.user, rumour):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "message": "Anda tidak memiliki izin untuk mengubah rumour ini."},
                status=403,
            )
        messages.error(request, "Anda tidak memiliki izin untuk mengubah rumour ini.")
        return redirect("transfer_rumour:detail", slug=rumour.slug)

    if request.method == "GET":
        form = TransferRumourForm(instance=rumour)
        form_html = render_to_string(
            "transfer_rumour/partials/form_fields.html",
            {"form": form},
            request=request,
        )
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "form_html": form_html,
                    "action": request.build_absolute_uri(),
                }
            )
        return redirect("transfer_rumour:detail", slug=rumour.slug)

    if request.method == "POST":
        form = TransferRumourForm(request.POST, instance=rumour)
        if form.is_valid():
            rumour = form.save()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Rumour berhasil diperbarui.",
                        "detail_url": rumour.get_absolute_url(),
                    }
                )
            messages.success(request, "Rumour berhasil diperbarui.")
            return redirect("transfer_rumour:detail", slug=rumour.slug)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            form_html = render_to_string(
                "transfer_rumour/partials/form_fields.html",
                {"form": form},
                request=request,
            )
            return JsonResponse(
                {"success": False, "form_html": form_html, "message": "Validasi gagal. Periksa isian Anda."},
                status=400,
            )
        messages.error(request, "Perbaruan rumour gagal. Periksa kembali input Anda.")
        return redirect("transfer_rumour:detail", slug=rumour.slug)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": False, "message": "Method tidak diperbolehkan."}, status=405)
    return redirect("transfer_rumour:detail", slug=rumour.slug)


@login_required
def rumour_delete(request, slug):
    rumour = get_object_or_404(TransferRumour, slug=slug)
    if not _can_manage_rumour(request.user, rumour):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "message": "Anda tidak memiliki izin untuk menghapus rumour ini."},
                status=403,
            )
        messages.error(request, "Anda tidak memiliki izin untuk menghapus rumour ini.")
        return redirect("transfer_rumour:detail", slug=rumour.slug)

    if request.method == "POST":
        rumour.delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": "Rumour berhasil dihapus.", "rumour_id": rumour.id})
        messages.success(request, "Rumour berhasil dihapus.")
        return redirect("transfer_rumour:list")

    return render(
        request,
        "transfer_rumour/confirm_delete.html",
        {
            "rumour": rumour,
        },
    )
