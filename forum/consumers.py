import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.group_name = f"notifications_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        unread_notifications = await self.get_unread_notifications()
        await self.send(text_data=json.dumps({
            "type": "initial_notifications",
            "notifications": unread_notifications,
            "unread_count": len([n for n in unread_notifications if not n["is_read"]])
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            
            if action == "mark_all_read":
                await self.mark_all_as_read()
                await self.send(text_data=json.dumps({
                    "type": "mark_read_success",
                    "unread_count": 0
                }))
            
            elif action == "get_notifications":
                notifications = await self.get_unread_notifications()
                await self.send(text_data=json.dumps({
                    "type": "notifications_list",
                    "notifications": notifications,
                    "unread_count": len([n for n in notifications if not n["is_read"]])
                }))
                
        except json.JSONDecodeError:
            pass

    async def send_notification(self, event):
        notification = event["notification"]
        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "notification": notification
        }))

    @database_sync_to_async
    def get_unread_notifications(self):
        notifs = Notification.objects.filter(
            recipient=self.user
        ).select_related("actor", "target_post", "target_comment")[:50]
        
        return [
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

    @database_sync_to_async
    def mark_all_as_read(self):
        Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True)
