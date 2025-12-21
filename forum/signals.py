from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Post, Comment, Notification


def send_notification_to_websocket(notification):
    channel_layer = get_channel_layer()
    group_name = f"notifications_{notification.recipient.id}"
    
    notification_data = {
        "id": notification.id,
        "actor": notification.actor.username,
        "verb": notification.verb,
        "post_id": notification.target_post.id if notification.target_post else None,
        "comment_id": notification.target_comment.id if notification.target_comment else None,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat()
    }
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "notification": notification_data
        }
    )


@receiver(m2m_changed, sender=Post.likes.through)
def notify_post_like(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            liker = instance.likes.get(pk=user_id)
            if liker != instance.author:
                notification = Notification.objects.create(
                    recipient=instance.author,
                    actor=liker,
                    verb="liked your post",
                    target_post=instance
                )
              
                send_notification_to_websocket(notification)


@receiver(m2m_changed, sender=Comment.likes.through)
def notify_comment_like(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            liker = instance.likes.get(pk=user_id)
            if liker != instance.user:
                notification = Notification.objects.create(
                    recipient=instance.user,
                    actor=liker,
                    verb="liked your comment",
                    target_comment=instance
                )
                send_notification_to_websocket(notification)


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
            notification = Notification.objects.create(
                recipient=target_user,
                actor=instance.user,
                verb=verb,
                target_post=instance.post,
                target_comment=instance.parent if instance.parent else None
            )
            send_notification_to_websocket(notification)