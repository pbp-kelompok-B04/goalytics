from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .forms import TransferRumourForm
from .models import TransferRumour

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import strip_tags
from django.views.decorators.http import require_GET, require_http_methods



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
@csrf_exempt
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

@require_GET
def rumour_list_json(request):
    rumours = (
        TransferRumour.objects
        .select_related("author", "author__profile")
        .all()
    )

    data = []
    for r in rumours:
        data.append({
            "id": r.id,
            "title": r.title,
            "slug": r.slug,
            "summary": r.summary,
            "content": r.content,
            "source_url": r.source_url,
            "cover_image_url": r.cover_image_url,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "author_username": r.author.username,
        })

    return JsonResponse(data, safe=False)


@require_GET
def rumour_detail_json(request, slug):
    rumour = get_object_or_404(
        TransferRumour.objects.select_related("author", "author__profile"),
        slug=slug,
    )

    data = {
        "id": rumour.id,
        "title": rumour.title,
        "slug": rumour.slug,
        "summary": rumour.summary,
        "content": rumour.content,
        "source_url": rumour.source_url,
        "cover_image_url": rumour.cover_image_url,
        "created_at": rumour.created_at.isoformat(),
        "updated_at": rumour.updated_at.isoformat(),
        "author_username": rumour.author.username,
    }

    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["POST"])
def create_rumour_flutter(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "Authentication required."},
            status=401,
        )

    if not _can_publish(request.user):
        return JsonResponse(
            {"status": "error", "message": "Anda tidak memiliki izin untuk membuat rumour."},
            status=403,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Body bukan JSON yang valid."},
            status=400,
        )

    title = strip_tags(data.get("title", "")).strip()
    summary = strip_tags(data.get("summary", "")).strip()
    content = strip_tags(data.get("content", "")).strip()
    source_url = data.get("source_url", "").strip()
    cover_image_url = data.get("cover_image_url", "").strip()

    if not title or not content:
        return JsonResponse(
            {"status": "error", "message": "Title dan content wajib diisi."},
            status=400,
        )

    rumour = TransferRumour.objects.create(
        title=title,
        summary=summary,
        content=content,
        source_url=source_url,
        cover_image_url=cover_image_url,
        author=request.user,
    )

    return JsonResponse(
        {
            "status": "success",
            "id": rumour.id,
            "slug": rumour.slug,
            "detail_url": rumour.get_absolute_url(),
        },
        status=200,
    )

@csrf_exempt
@require_http_methods(["POST", "PUT", "PATCH"])
def update_rumour_flutter(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "Authentication required."},
            status=401,
        )

    rumour = get_object_or_404(TransferRumour, slug=slug)

    if not _can_manage_rumour(request.user, rumour):
        return JsonResponse(
            {"status": "error", "message": "Anda tidak memiliki izin untuk mengubah rumour ini."},
            status=403,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Body bukan JSON yang valid."},
            status=400,
        )

    if "title" in data:
        rumour.title = strip_tags(data["title"]).strip()
    if "summary" in data:
        rumour.summary = strip_tags(data["summary"]).strip()
    if "content" in data:
        rumour.content = strip_tags(data["content"]).strip()
    if "source_url" in data:
        rumour.source_url = data["source_url"].strip()
    if "cover_image_url" in data:
        rumour.cover_image_url = data["cover_image_url"].strip()

    rumour.save()

    return JsonResponse(
        {
            "status": "success",
            "message": "Rumour berhasil diperbarui.",
            "slug": rumour.slug,
        },
        status=200,
    )
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def delete_rumour_flutter(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "Authentication required."},
            status=401,
        )

    rumour = get_object_or_404(TransferRumour, slug=slug)

    if not _can_manage_rumour(request.user, rumour):
        return JsonResponse(
            {"status": "error", "message": "Anda tidak memiliki izin untuk menghapus rumour ini."},
            status=403,
        )

    rumour_id = rumour.id
    rumour.delete()

    return JsonResponse(
        {
            "status": "success",
            "message": "Rumour berhasil dihapus.",
            "id": rumour_id,
        },
        status=200,
    )
