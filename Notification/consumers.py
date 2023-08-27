from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from Authentication.models import CustomUser
from Notification.models import Notifications
from django.db.models import Q
from helpers.utils import get_notifications

class UserNotificationConsumer(JsonWebsocketConsumer):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def connect(self):
        self.user_id = self.scope["auth_user"]["user_id"]
        self.user = CustomUser.objects.get(id=self.user_id)
        self.accept()

        self.notification_group_name = "user_notifications"
        async_to_sync(self.channel_layer.group_add)(
            self.notification_group_name,
            self.channel_name,
        )

        self.send_notification_data()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.notification_group_name,
            self.channel_name,
        )
        return super().disconnect(code)

    def receive_json(self, content, **kwargs):
        message_type = content.get('type')
        delete_id = content.get('delete_id')

        if message_type == 'mark_all_as_read':
            # Mark all notifications as read in the database
            Notifications.objects.filter(user_id=self.user_id, read=False, notification_type='user notification').update(read=True)

            # Send a success response back to the frontend
            self.send_json({
                'type': 'mark_all_as_read',
                'message': 'All notifications marked as read successfully.',
            })
        elif delete_id:
            try:
                notification = Notifications.objects.get(id=delete_id, user_id=self.user_id)
                notification.delete()

                # Send a success response back to the frontend
                self.send_json({
                    'type': 'delete_notification',
                    'message': 'Notification deleted successfully.',
                })
            except Notifications.DoesNotExist:
                # Send an error response if the notification does not exist
                self.send_json({
                    'type': 'delete_notification',
                    'error': 'Notification not found.',
                })

        self.send_notification_data()

    def send_notification_data(self):
        notif = get_notifications(self.user)

        async_to_sync(self.channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_notification',
                'notification': notif
            }
        )

        count_user_notifs = Notifications.objects.filter(Q(read=False) & Q(notification_type='user notification') & Q(user_id=self.user_id)).count()

        async_to_sync(self.channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_notification_count',
                'unread_count': count_user_notifs
            }
        )

    def user_notification(self, event):
        self.send_json(event)

    def user_notification_count(self, event):
        self.send_json(event)


from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json

class UserNotificationConsumer(AsyncJsonWebsocketConsumer):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    async def connect(self):
        self.user = self.scope["user"]

        await self.channel_layer.group_add(
            self.get_notification_group_name(self.user.id),
            self.channel_name,
        )

        await self.accept()

        await self.send_notification_data()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.get_notification_group_name(self.user.id),
            self.channel_name,
        )

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')
        delete_id = content.get('delete_id')

        if message_type == 'mark_all_as_read':
            await self.mark_all_notifications_as_read()

            # Send a success response back to the frontend
            await self.send_json({
                'type': 'mark_all_as_read',
                'message': 'All notifications marked as read successfully.',
            })
        elif delete_id:
            await self.delete_notification(delete_id)

    async def send_notification_data(self):
        notifications = await self.get_notifications()

        await self.send_json({
            'type': 'user_notification',
            'notification': notifications
        })

        unread_count = await self.get_unread_notification_count()

        await self.send_json({
            'type': 'user_notification_count',
            'unread_count': unread_count
        })

    @database_sync_to_async
    def get_notification_group_name(self, user_id):
        return f"user_{user_id}"

    @database_sync_to_async
    def mark_all_notifications_as_read(self):
        Notifications.objects.filter(user_id=self.user.id, read=False, notification_type='user notification').update(read=True)

    @database_sync_to_async
    def delete_notification(self, delete_id):
        try:
            notification = Notifications.objects.get(id=delete_id, user_id=self.user.id)
            notification.delete()
        except Notifications.DoesNotExist:
            pass

    @database_sync_to_async
    def get_notifications(self):
        return get_notifications(self.user)

    @database_sync_to_async
    def get_unread_notification_count(self):
        return Notifications.objects.filter(Q(read=False) & Q(notification_type='user notification') & Q(user_id=self.user.id)).count()
