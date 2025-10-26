from django.shortcuts import render
from .models import Post, Comment, LEAGUE_CHOICES, Notification
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.views.decorators.http import require_http_methods
from urllib.parse import quote
import json
def _avatar_for_user(user):
    profile = getattr(user, "profile", None)
    avatar = getattr(profile, "profile_picture", None) if profile else None
    if avatar:
        return avatar
    fallback_source = (user.get_full_name() or "").strip() or user.username or "User"
    return f"https://ui-avatars.com/api/?name={quote(fallback_source)}"

def forum_home(request):
    is_admin = False
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if getattr(profile, "role", "") == "admin":
            is_admin = True
    context = {
        "forum_is_admin": is_admin,
    }
    return render(request, "forum_home.html", context)

def forum_post_detail(request, post_id):
    return render(request, "post_detail.html", {"post_id": post_id})

# Create your views here.
@require_http_methods(["GET"])
def get_all_post(request):
    qs = Post.objects.select_related("author", "author__profile")
    league = request.GET.get("league")
    if league:
        valid_codes = {code for code, _ in LEAGUE_CHOICES}
        if league in valid_codes:
            qs = qs.filter(league=league)
    mine = request.GET.get("mine")
    if mine and request.user.is_authenticated:
        if mine.lower() in {"true", "1", "yes", "on"}:
            qs = qs.filter(author=request.user)
    sort = request.GET.get("sort", "newest")
    order_field = "created_at" if sort == "oldest" else "-created_at"
    all_post = (
        qs.annotate(
            comment_count=Count("comments", distinct=True),
            like_count=Count("likes", distinct=True),
        )
        .order_by(order_field)
    )
    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(request.user.liked_post.values_list("id", flat=True))
    data = []
    for p in all_post:
        post = {
            'id': p.id,
            'author': p.author.username,
            'title': p.title,
            'content': p.content,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "comment_count": (getattr(p, "comment_count", 0) or 0),
            "league": p.league,
            "is_author": request.user.is_authenticated and p.author == request.user,
            "like_count": getattr(p, "like_count", 0),
            "is_liked": p.id in liked_post_ids,
            "avatar": _avatar_for_user(p.author),
            "media_url": p.media_url or None,
            "attachment_url": (getattr(p.attachment, "url", None) if p.attachment else None)
        }
        data.append(post)
    return JsonResponse({"data": data})

@require_http_methods(["GET"])
def get_post_by_id(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "author__profile").annotate(
            comment_count=Count("comments", distinct=True),
            like_count=Count("likes", distinct=True),
        ),
        id=post_id,
    )
    liked = False
    if request.user.is_authenticated:
        liked = post.likes.filter(id=request.user.id).exists()
    data = {
        'id': post.id,
        'author': post.author.username,
        'title': post.title,
        'content': post.content,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "comment_count": (getattr(post, "comment_count", 0) or 0),
        "league": post.league,
        "avatar": _avatar_for_user(post.author),
        "is_author": request.user.is_authenticated and post.author == request.user,
        "like_count": getattr(post, "like_count", 0),
        "is_liked": liked,
        "media_url": post.media_url or None,
        "attachment_url": (getattr(post.attachment, "url", None) if post.attachment else None)
    }
    return JsonResponse({"data": data})

@require_http_methods(["GET"])
def get_post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user if request.user.is_authenticated else None
    liked_comment_ids = set()
    if user:
        liked_comment_ids = set(user.liked_comment.values_list("id", flat=True))
    comments = (
        post.comments
        .select_related("user", "user__profile")
        .prefetch_related("likes")
        .annotate(like_count=Count("likes", distinct=True))
        .order_by("created_at")
    )

    comment_lookup = {}
    created_lookup = {}
    for comment in comments:
        comment_lookup[comment.id] = {
            "id": comment.id,
            "user": comment.user.username,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "parent_id": comment.parent_id,
            "replies": [],
            "is_owner": bool(user and comment.user_id == user.id),
            "like_count": getattr(comment, "like_count", comment.likes.count()),
            "is_liked": comment.id in liked_comment_ids,
            "avatar": _avatar_for_user(comment.user),
        }
        created_lookup[comment.id] = comment.created_at

    roots = []
    for comment in comments:
        data = comment_lookup[comment.id]
        if comment.parent_id:
            parent = comment_lookup.get(comment.parent_id)
            if parent is not None:
                parent["replies"].append(data)
        else:
            roots.append((comment.created_at, data))

    def sort_replies(node):
        node["replies"].sort(key=lambda item: created_lookup.get(item["id"]))
        for child in node["replies"]:
            sort_replies(child)

    for _, root_data in roots:
        sort_replies(root_data)

    roots.sort(key=lambda item: item[0], reverse=True)
    serialized = [item[1] for item in roots]
    return JsonResponse({"data": serialized})

@login_required
@require_http_methods(["GET"])
def get_my_posts(request):
    qs = (
        Post.objects.select_related("author", "author__profile")
        .filter(author=request.user)
    )
    league = request.GET.get("league")
    if league:
        valid_codes = {code for code, _ in LEAGUE_CHOICES}
        if league in valid_codes:
            qs = qs.filter(league=league)
    sort = request.GET.get("sort", "newest")
    order_field = "created_at" if sort == "oldest" else "-created_at"
    all_post = (
        qs.annotate(
            comment_count=Count("comments", distinct=True),
            like_count=Count("likes", distinct=True),
        )
        .order_by(order_field)
    )
    liked_post_ids = set(request.user.liked_post.values_list("id", flat=True))
    data = []
    for p in all_post:
        post = {
            'id': p.id,
            'author': p.author.username,
            'title': p.title,
            'content': p.content,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "comment_count": (getattr(p, "comment_count", 0) or 0),
            "league": p.league,
            "is_author": True,
            "like_count": getattr(p, "like_count", 0),
            "is_liked": p.id in liked_post_ids,
            "avatar": _avatar_for_user(p.author),
        }
        data.append(post)
    return JsonResponse({"data": data})

@login_required
@require_http_methods(["POST"])
def create_post(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()
    league = (payload.get("league") or "").strip().upper()
    media_url = (payload.get("media_url") or "").strip()
    if not title or not content:
        return JsonResponse({"error": "title dan content wajib diisi"}, status=400)
    if not title or not content:
        return JsonResponse({"error": "title dan content wajib diisi"}, status=400)
    valid_codes = {code for code, _ in LEAGUE_CHOICES}
    if league and league not in valid_codes:
        return JsonResponse({"error": "league tidak valid"}, status=400)

    p = Post.objects.create(
        author=request.user,
        title=title,
        content=content,
        league=league or "EPL",
        media_url=media_url or None,
    )
    data = {
        'id': p.id,
        'author': p.author.username,
        'title': p.title,
        'content': p.content,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "comment_count": 0,
        "league": p.league,
        "is_author": True,
        "like_count": 0,
        "is_liked": False,
        "avatar": _avatar_for_user(p.author),
        'media_url': p.media_url
    }
    return JsonResponse({"data": data}, status=201)

@login_required
@require_http_methods(["POST"])
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    payload = json.loads(request.body.decode("utf-8"))
    content = (payload.get("content") or "").strip()
    parent_id = payload.get("parent_id")
    if not content:
        return JsonResponse({"error": "content wajib diisi"}, status=400)
    parent = None
    if parent_id:
        parent = Comment.objects.filter(id=parent_id, post=post).first()
        if parent_id and parent is None:
            return JsonResponse({"error": "parent_id tidak valid untuk post ini"}, status=400)
    c = Comment.objects.create(post=post, user=request.user, content=content, parent=parent)
    data = {
        "id": c.id,
        "user": c.user.username,
        "content": c.content,
        "created_at": c.created_at.isoformat(),
        "parent_id": c.parent_id,
        "is_owner": True,
        "like_count": 0,
        "is_liked": False,
        "avatar": _avatar_for_user(c.user),
    }
    return JsonResponse({"data": data}, status=201)

@login_required
@require_http_methods(["POST"])
def like_post(request, post_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    if payload.get('_method') != 'PATCH':
        return JsonResponse({'error': 'Method override required'}, status=405)
    post_id = payload.get('post_id')
    if not post_id:
        return JsonResponse({'error': 'post_id wajib dikirim'}, status=400)
    post = get_object_or_404(Post, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'like_count': post.likes.count(),
    }, status=200)
    
@login_required
@require_http_methods(["POST"])
def like_comment(request, comment_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    if payload.get('_method') != 'PATCH':
        return JsonResponse({'error': 'Method override required'}, status=405)
    post_id = payload.get('post_id')
    comment_id = payload.get('comment_id')
    if not post_id or not comment_id:
        return JsonResponse({'error': 'post_id dan comment_id wajib dikirim'}, status=400)
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'like_count': comment.likes.count(),
    }, status=200)

@login_required
@require_http_methods(["POST"])
def update_post(request, post_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    if payload.get('_method') != 'PATCH':
        return JsonResponse({'error': 'Method override required'}, status=405)

    post_id = payload.get('post_id')
    if not post_id:
        return JsonResponse({"error": "post_id wajib dikirim"}, status=400)
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return JsonResponse({"error": "forbidden"}, status=400)

    if 'title' in payload:
        post.title = (payload.get('title') or '').strip()
    if 'content' in payload:
        post.content = (payload.get('content') or '').strip()
    if 'league' in payload:
        league = (payload.get('league') or '').strip().upper()
        if league:
            valid_codes = {code for code, _ in LEAGUE_CHOICES}
            if league not in valid_codes:
                return JsonResponse({"error": "league tidak valid"}, status=400)
            post.league = league
    post.save()
    return JsonResponse({
        "message": "Post updated successfully",
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "league": post.league,
    })

@login_required
@require_http_methods(["POST"])
def update_comment(request, comment_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
        post_id = data['post_id']
        comment_id = data['comment_id']
        new_content = data['content'].strip()
    except (json.JSONDecodeError, AttributeError, KeyError):
        return JsonResponse({'error': 'JSON tidak valid'}, status=400)
    if data.get('_method') != 'PATCH':
        return JsonResponse({'error': 'Method override required'}, status=405)
    if not new_content:
        return JsonResponse({'error': 'Isi komentar tidak boleh kosong'}, status=400)
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if comment.user != request.user:
        return JsonResponse({'error': 'forbidden'}, status=400)
    comment.content = new_content
    comment.save()
    return JsonResponse({
        'status': 'success',
        'comment_id': comment.id,
        'new_content': comment.content,
        'updated_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@login_required
@require_http_methods(["POST"])
def delete_post(request, post_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    if payload.get('_method') != 'DELETE':
        return JsonResponse({'error': 'Method override required'}, status=405)
    post_id = payload.get('post_id')
    if not post_id:
        return JsonResponse({'error': 'post_id wajib dikirim'}, status=400)
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return JsonResponse({'error': 'forbidden'}, status=400)
    post.delete()
    return JsonResponse({
        'message': 'Post berhasil dihapus'
    }, status=200)

@login_required
@require_http_methods(["POST"])
def delete_comment(request, comment_id):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
    if payload.get('_method') != 'DELETE':
        return JsonResponse({'error': 'Method override required'}, status=405)
    post_id = payload.get('post_id')
    comment_id = payload.get('comment_id')
    if not post_id:
        return JsonResponse({'error': 'post_id wajib dikirim'}, status=400)
    if not comment_id:
        return JsonResponse({'error': 'comment_id wajib dikirim'}, status=400)
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if comment.user != request.user:
        return JsonResponse({'error': 'forbidden'}, status=400)
    comment.delete()
    return JsonResponse({
        'message': 'Komentar berhasil dihapus'
    }, status=200)


@login_required
def get_notifications(request):
    notifs = Notification.objects.filter(recipient=request.user).select_related("actor", "target_post", "target_comment")[:50]
    data = [
        {
            "id": n.id,
            "actor": n.actor.username,
            "verb": n.verb,
            "post_id": n.target_post.id if n.target_post else None,
            "comment_id": n.target_comment.id if n.target_comment else None,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        }
        for n in notifs
    ]
    return JsonResponse({"data": data})

@login_required
@require_http_methods(["POST"])
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"message": "All notifications marked as read"})

@login_required
@require_http_methods(["POST"])
def upload_attachment(request):
    file = request.FILES.get("attachment")
    if not file:
        return JsonResponse({"error": "file tidak ditemukan"}, status=400)

    post = Post.objects.create(author=request.user, title="(upload-only)", content="")
    post.attachment = file
    post.save()

    return JsonResponse({
        "attachment_url": post.attachment.url,
        "post_id": post.id,
        "url": post.attachment.url
    }, status=201)
