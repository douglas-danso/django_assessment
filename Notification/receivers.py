from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from Notification.models import Notifications
from User_Relationship.signals import get_new_followers, get_new_comments,like_a_post,like_a_comment
from django.db.models import Q

@receiver(get_new_followers)
def followers_notification(sender,receiver,sender_user):
    channel_layer = get_channel_layer()
    details = {
        'user':receiver,
        'sender':sender_user,
        'detail':f'{sender_user} has followed you',
        'notification_type':'user notifications'
    }

    notification = Notifications.objects.create(**details)

    message ={
        "id" : notification.id,
        "name" : sender_user.first_name + " " + sender_user.last_name,
        "profile_picture" : sender_user.profile_picture,
        "detail" : notification.detail,
        "read" : notification.read,
        "timestamp" : str(notification.timestamp)
    }
    async_to_sync(channel_layer.group_send)(
        'user_notifications', 
        {
         'type': 'user notification', 
         'notification': message
        }
    )
    
    notifications_filter = Q(read=False, user_id=receiver.id, notification_type='user notification')
    count_notifs = Notifications.objects.filter(notifications_filter).count()

    async_to_sync(channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_notification_count',
                'unread_count': count_notifs
            }
        )


@receiver(get_new_comments)
def new_comments_notification(sender,sender_user,post):
    channel_layer = get_channel_layer()
    details = {
        'user':post.user,
        'sender':sender_user,
        'detail':f'{sender_user} has commented on your {post}',
        'notification_type':'user notifications'
    }

    notification = Notifications.objects.create(**details)

    message ={
        "id" : notification.id,
        "name" : sender_user.first_name + " " + sender_user.last_name,
        "profile_picture" : sender_user.profile_picture,
        "detail" : notification.detail,
        "read" : notification.read,
        "timestamp" : str(notification.timestamp)
    }
    async_to_sync(channel_layer.group_send)(
        'user_notifications', 
        {
         'type': 'user notification', 
         'notification': message
        }
    )
    
    notifications_filter = Q(read=False, user_id=post.user.id, notification_type='user notification')
    count_notifs = Notifications.objects.filter(notifications_filter).count()

    async_to_sync(channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_notification_count',
                'unread_count': count_notifs
            }
        )
@receiver(like_a_post)
def like_posts_notification(sender,sender_user,post):
    channel_layer = get_channel_layer()
    details = {
        'user':post.user,
        'sender':sender_user,
        'detail':f'{sender_user} has liked {post}',
        'notification_type':'user notifications'
    }

    notification = Notifications.objects.create(**details)

    message ={
        "id" : notification.id,
        "name" : sender_user.first_name + " " + sender_user.last_name,
        "profile_picture" : sender_user.profile_picture,
        "detail" : notification.detail,
        "read" : notification.read,
        "timestamp" : str(notification.timestamp)
    }
    async_to_sync(channel_layer.group_send)(
        'user_notifications', 
        {
         'type': 'user notification', 
         'notification': message
        }
    )
    
    notifications_filter = Q(read=False, user_id=post.user.id, notification_type='user notification')
    count_notifs = Notifications.objects.filter(notifications_filter).count()

    async_to_sync(channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_notification_count',
                'unread_count': count_notifs
            }
        )
    
@receiver(like_a_comment)
def like_comments_notification(sender,sender_user,comment):
    channel_layer = get_channel_layer()
    details = {
        'user':comment.user,
        'sender':sender_user,
        'detail':f'{sender_user} has liked {comment}',
        'notification_type':'user notifications'
    }

    notification = Notifications.objects.create(**details)

    message ={
        "id" : notification.id,
        "name" : sender_user.first_name + " " + sender_user.last_name,
        "profile_picture" : sender_user.profile_picture,
        "detail" : notification.detail,
        "read" : notification.read,
        "timestamp" : str(notification.timestamp)
    }
    async_to_sync(channel_layer.group_send)(
        'user_notifications', 
        {
         'type': 'user notification', 
         'notification': message
        }
    )
    
    notifications_filter = Q(read=False, user_id=comment.user.id, notification_type='user notification')
    count_notifs = Notifications.objects.filter(notifications_filter).count()

    async_to_sync(channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_notification_count',
                'unread_count': count_notifs
            }
        )