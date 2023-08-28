from celery import shared_task
from django.core.mail import send_mail
from Authentication.models import CustomUser
from django.urls import reverse
import json
from helpers.utils import encode_token
import cloudinary
from rest_framework.views import status
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator


@shared_task
def send_activation_email_async(request_data, user_data):
    email = user_data['email']
    full_name = user_data['full_name']
    
    token = encode_token(email=email)
    activation_link = reverse('activate', kwargs={'token': token})
    activation_url = f'http://{request_data["host"]}{activation_link}'
    message = f'Hi {full_name}, please click on this link to activate your account: {activation_url}'
    
    send_mail(
        'Activate your account',
        message,
        'douglasdanso66@gmail.com',
        [email],
        fail_silently=False,
    )
@shared_task
def send_passwordreset_email_async(request_data, user_data):
    email = user_data['email']
    full_name = user_data['full_name']
    user = get_object_or_404(CustomUser,email=email)
    
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = request_data["uri"](
                reverse('passwordresetconfirm', kwargs={'uidb64': uidb64, 'token': token}))
        # Send the reset URL to the user by email
    subject = 'Password reset'
    message = f'Use this link to reset your password: {reset_url}'
    from_email = 'douglasdanso66@gmail.com'
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

@shared_task
def delete_cloudinary_file_async(public_id):
    try:
        # Delete the file from Cloudinary
        cloudinary.uploader.destroy(public_id)
            
    except cloudinary.api.Error as e:
        pass
    return {"detail": "File deleted successfully"}