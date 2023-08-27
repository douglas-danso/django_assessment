from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.sites.shortcuts import get_current_site
from Authentication.models import CustomUser
from django.urls import reverse
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_encode
import jwt
from helpers.utils import encode_token

def send_activation_email(request, user):
    email = user.email
    token = encode_token(email=email)
    activation_link = reverse('activate', kwargs={'token': token})
    activation_url = f'http://{request.get_host()}{activation_link}'
    message = f'Hi {user.full_name}, please click on this link to activate your account: {activation_url}'
    send_mail(
        'Activate your account',
        message,
        'douglasdanso66@gmail.com',
        [user.email],
        fail_silently=False,
    )

