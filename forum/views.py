from django.shortcuts import render
from .models import Post, Comment, LEAGUE_CHOICES
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.views.decorators.http import require_http_methods
import json


def forum_home(request):
    return render(request, "forum_home.html")

def forum_post_detail(request, post_id):
    return render(request, "post_detail.html", {"post_id": post_id})

# Create your views here.
@require_http_methods(["GET"])
def get_all_post(request):
    qs = Post.objects.all()
    league = request.GET.get("league")
    if league:
        valid_codes = {code for code, _ in LEAGUE_CHOICES}
        if league in valid_codes:
            qs = qs.filter(league=league)
    all_post = qs.order_by("-created_at").annotate(comment_count=Count("comments"))
    data = []
    for p in all_post:
        post = {
            'id': p.id,
            'author': p.author.username,
            'title': p.title,
            'content': p.content,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "comment_count": getattr(p, "comment_count", None),
            "league": p.league,
        }
        data.append(post)
    return JsonResponse({"data": data})


@require_http_methods(["GET", "POST"])
def posts_collection(request):
    if request.method == "GET":
        return get_all_post(request)
    return create_post(request)


@require_http_methods(["GET", "PATCH", "DELETE"])
def post_detail(request, post_id):
    if request.method == "GET":
        return get_post_by_id(request, post_id)
    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    payload = payload or {}
    payload["post_id"] = post_id
    request._body = json.dumps(payload).encode("utf-8")
    if request.method == "PATCH":
        return update_post(request)
    return delete_post(request)


@require_http_methods(["POST", "DELETE"])
def post_likes(request, post_id):
    if request.method == "POST":
        try:
            payload = json.loads((request.body or b"{}").decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        payload["post_id"] = post_id
        request._body = json.dumps(payload).encode("utf-8")
        return like_post(request)
    post = get_object_or_404(Post, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    return JsonResponse({"liked": False}, status=200)


@require_http_methods(["GET", "POST"])
def comments_collection(request, post_id):
    if request.method == "GET":
        return get_post_comment(request, post_id)
    return create_comment(request, post_id)


@require_http_methods(["PATCH", "DELETE"])
def comment_detail(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related("post"), id=comment_id)
    post_id = comment.post_id
    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    payload = payload or {}
    payload["post_id"] = post_id
    payload["comment_id"] = comment_id
    request._body = json.dumps(payload).encode("utf-8")

    if request.method == "PATCH":
        return update_comment(request)
    # DELETE
    return delete_comment(request)


@require_http_methods(["POST", "DELETE"])
def comment_likes(request, comment_id):
    # Resolve post id
    comment = get_object_or_404(Comment.objects.select_related("post"), id=comment_id)
    post_id = comment.post_id

    if request.method == "POST":
        try:
            payload = json.loads((request.body or b"{}").decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        payload["post_id"] = post_id
        payload["comment_id"] = comment_id
        request._body = json.dumps(payload).encode("utf-8")
        return like_comment(request)

    # DELETE -> ensure unlike
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
    return JsonResponse({"liked": False}, status=200)

@require_http_methods(["GET"])
def get_post_by_id(request, post_id):
    post = get_object_or_404(Post.objects.annotate(comment_count=Count("comments")),id=post_id)
    data = {
        'id': post.id,
        'author': post.author.username,
        'title': post.title,
        'content': post.content,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "comment_count": getattr(post, "comment_count", None),
        "league": post.league,
    }
    return JsonResponse({"data": data})

@require_http_methods(["GET"])
def get_post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Pull every comment for this post once to avoid recursive queries
    comments = (
        post.comments
        .select_related("user")
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

    # Replies were appended in chronological order; maintain that for nested
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
    qs = Post.objects.filter(author=request.user)
    league = request.GET.get("league")
    if league:
        valid_codes = {code for code, _ in LEAGUE_CHOICES}
        if league in valid_codes:
            qs = qs.filter(league=league)
    all_post = qs.order_by("-created_at").annotate(comment_count=Count("comments"))
    data = []
    for p in all_post:
        post = {
            'id': p.id,
            'author': p.author.username,
            'title': p.title,
            'content': p.content,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "comment_count": getattr(p, "comment_count", None),
            "league": p.league,
        }
        data.append(post)
    return JsonResponse({"data": data})

@login_required
@require_http_methods(["POST"])
def create_post(request):
    payload = json.loads(request.body.decode("utf-8"))
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()
    league = (payload.get("league") or "").strip().upper()
    if not title or not content:
        return JsonResponse({"error": "title dan content wajib diisi"}, status=400)
    valid_codes = {code for code, _ in LEAGUE_CHOICES}
    kwargs = {"author": request.user, "title": title, "content": content}
    if league:
        if league not in valid_codes:
            return JsonResponse({"error": "league tidak valid"}, status=400)
        kwargs["league"] = league
    p = Post.objects.create(**kwargs)
    data = {
        'id': p.id,
        'author': p.author.username,
        'title': p.title,
        'content': p.content,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "comment_count": getattr(p, "comment_count", None),
        "league": p.league,
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
    }
    return JsonResponse({"data": data}, status=201)

@login_required
@require_http_methods(["PATCH"])
def like_post(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
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
    }, status=200)
    
@login_required
@require_http_methods(["PATCH"])
def like_comment(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
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
        'liked': liked
    }, status=200)

@login_required
@require_http_methods(["PATCH"])
def update_post(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)

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
@require_http_methods(["PATCH"])
def update_comment(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        post_id = data['post_id']
        comment_id = data['comment_id']
        new_content = data['content'].strip()
    except (json.JSONDecodeError, AttributeError, KeyError):
        return JsonResponse({'error': 'JSON tidak valid'}, status=400)
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
@require_http_methods(["DELETE"])
def delete_post(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
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
@require_http_methods(["DELETE"])
def delete_comment(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid JSON'}, status=400)
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


