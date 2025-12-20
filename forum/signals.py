from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Post, Comment, Notification

@receiver(m2m_changed, sender=Post.likes.through)
def notify_post_like(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            liker = instance.likes.get(pk=user_id)
            if liker != instance.author:
                Notification.objects.create(
                    recipient=instance.author,
                    actor=liker,
                    verb="liked your post",
                    target_post=instance
                )

@receiver(m2m_changed, sender=Comment.likes.through)
def notify_comment_like(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            liker = instance.likes.get(pk=user_id)
            if liker != instance.user:
                Notification.objects.create(
                    recipient=instance.user,
                    actor=liker,
                    verb="liked your comment",
                    target_comment=instance
                )

@receiver(post_save, sender=Comment)
def notify_new_comment(sender, instance, created, **kwargs):
    if created:
        if instance.parent:
            target_user = instance.parent.user
            verb = "replied to your comment"
        else:
            target_user = instance.post.author
            verb = "commented on your post"
        if target_user != instance.user:
            Notification.objects.create(
                recipient=target_user,
                actor=instance.user,
                verb=verb,
                target_post=instance.post,
                target_comment=instance.parent if instance.parent else None
            )
#tes