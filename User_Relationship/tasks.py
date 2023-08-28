
from celery import shared_task
from django.core.mail import send_mail
import cloudinary
from .models import Posts,Comments
from cloudinary import uploader
import os 
from Authentication.models import CustomUser

@shared_task
def send_notification_email(user_email, notification_type, post_content):
    subject = "New Notification on Your Post"
    message = f"Your post has received a {notification_type}: {post_content}"
    from_email = "your@example.com"
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


@shared_task
def send_follow_notification_email(user_email, follower_name):
    subject = "New Follower Notification"
    message = f"{follower_name} started following you."
    from_email = "your@example.com"
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

@shared_task
def async_upload_file(temp_file_path, content, post_privacy, user_id,resource_type):
    try:
        with open(temp_file_path, 'rb') as temp_file:
            
            cloudinary_response = uploader.upload(temp_file, resource_type=resource_type)
            file_url = cloudinary_response['secure_url']
    except (cloudinary.exceptions.Error, FileNotFoundError):
        return
    finally:
        # Delete the temporary file
        os.remove(temp_file_path)
    
    user = CustomUser.objects.get(id=user_id)
    Posts.objects.create(file=file_url, content=content, user=user, post_privacy=post_privacy)

@shared_task
def async_upload_file_comment(temp_file_path, comment, user_id,resource_type,post_id,id):
    try:
        with open(temp_file_path, 'rb') as temp_file:
            
            cloudinary_response = uploader.upload(temp_file, resource_type=resource_type)
            file_url = cloudinary_response['secure_url']
    except (cloudinary.exceptions.Error, FileNotFoundError):
        return
    finally:
        # Delete the temporary file
        os.remove(temp_file_path)
    
    user = CustomUser.objects.get(id=user_id)
    if id:
            comment =Comments.objects.create(file=file_url, comment=comment, comment_user=user,post_id=post_id)
            try:
                parent_comment = Comments.objects.get(id=id)
                comment.parent_comment = parent_comment
                comment.save()
            except Comments.DoesNotExist:
                pass
    else:
        Comments.objects.create(file=file_url, comment=comment, comment_user=user,post_id=post_id)
