from django.shortcuts import render
from .models import Post, Comment
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
import json


def forum_home(request):
    """Render forum landing page that consumes JSON endpoints via JS."""
    return render(request, "forum/forum.html")

# Create your views here.
@require_http_methods(["GET"])
def get_all_post(request):
    all_post = Post.objects.all().order_by("-created_at").annotate(comment_count=Count("comments"))
    data = []
    for p in all_post:
        post = {
            'id': p.id,
            'author': p.author.username,
            'title': p.title,
            'content': p.content,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "comment_count": getattr(p, "comment_count", None)
        }
        data.append(post)
    return JsonResponse({"data": data})

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
        "comment_count": getattr(post, "comment_count", None)
    }
    return JsonResponse({"data": data})

@require_http_methods(["GET"])
def get_post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent__isnull=True).order_by("-created_at")
    data = []
    for c in comments:
        replies = c.replies.all().order_by("created_at")
        comment = {
            "id": c.id,
            "user": c.user.username,
            "content": c.content,
            "created_at": c.created_at.isoformat(),
            "parent_id": c.parent_id,
            "replies": [
                {
                    "id": r.id,
                    "user": r.user.username,
                    "content": r.content,
                    "created_at": r.created_at.isoformat(),
                    "parent_id": r.parent_id,
                }
                for r in replies
            ]
        }
        data.append(comment)
    return JsonResponse({"data": data})

@login_required
@require_http_methods(["GET"])
def get_my_posts(request):
    all_post = Post.objects.filter(author=request.user).order_by("-created_at").annotate(comment_count=Count("comments"))
    data = []
    for p in all_post:
        post = {
            'id': p.id,
            'author': p.author.username,
            'title': p.title,
            'content': p.content,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "comment_count": getattr(p, "comment_count", None)
        }
        data.append(post)
    return JsonResponse({"data": data})

@login_required
@require_http_methods(["POST"])
def create_post(request):
    payload = json.loads(request.body.decode("utf-8"))
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()
    if not title or not content:
        return JsonResponse({"error": "title dan content wajib diisi"}, status=400)
    p = Post.objects.create(author=request.user, title=title, content=content)
    data = {
        'id': p.id,
        'author': p.author.username,
        'title': p.title,
        'content': p.content,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "comment_count": getattr(p, "comment_count", None)
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
        post_id = payload['post_id']
    except:
        post_id = None
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
        post_id = payload['post_id']
        comment_id = payload['comment_id']
    except:
        post_id = None
        comment_id = None
    post = get_object_or_404(Post, id=post_id)
    comment=get_object_or_404(Comment, id=comment_id, post=post)
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
        post_id = payload['post_id']
    except:
        post_id = None

    post = get_object_or_404(Post, id=post_id)
    data = json.loads(request.body.decode('utf-8'))
    if 'title' in data:
        post.title = data['title'].strip()
    if 'content' in data:
        post.content = data['content'].strip()
    post.save()
    return JsonResponse({
        "message": "Post updated successfully",
        "id": post.id,
        "title": post.title,
        "content": post.content,
    })


@login_required
@require_http_methods(["PATCH"])
def update_comment(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        post_id = data['post_id']
        comment_id = data['comment_id']
        new_content = data['content'].strip()
    except (json.JSONDecodeError, AttributeError):
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
        post_id = payload['post_id']
    except:
        post_id = None
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
        post_id = payload['post_id']
        comment_id = payload['comment_id']
    except:
        post_id = None
        comment_id = None
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
        'message': 'Post berhasil dihapus'
    }, status=200)

