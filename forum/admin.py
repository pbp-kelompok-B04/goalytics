from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "league", "created_at", "updated_at", "like_count", "comment_total")
    list_filter = ("league", "created_at", "updated_at")
    search_fields = ("title", "content", "author__username")
    autocomplete_fields = ("author", "likes")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def like_count(self, obj):
        return obj.likes.count()

    like_count.short_description = "Likes"

    def comment_total(self, obj):
        return obj.comments.count()

    comment_total.short_description = "Comments"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_content", "user", "post", "parent", "created_at", "like_count")
    list_filter = ("created_at", "post__league")
    search_fields = ("content", "user__username", "post__title")
    autocomplete_fields = ("post", "user", "parent", "likes")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def short_content(self, obj):
        return (obj.content[:60] + "...") if len(obj.content) > 60 else obj.content

    short_content.short_description = "Content"

    def like_count(self, obj):
        return obj.likes.count()

    like_count.short_description = "Likes"
