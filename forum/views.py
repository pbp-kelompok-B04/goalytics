from django.shortcuts import render
from .models import Post, Comment
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods

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
    return JsonResponse({data: data})

@require_http_methods(["GET"])
def get_post_by_id(request, post_id):
    post = get_object_or_404(Post.objects.annotate(comment_count=Count("comments")),id=post_id)
    data = {
        'id': p.id,
            'author': post.author.username,
            'title': post.title,
            'content': post.content,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "comment_count": getattr(post, "comment_count", None)
    }
    return JsonResponse({data: data})

