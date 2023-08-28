# from celery import shared_task

# def send_follow_email(user):
#     email = user.email
#     token = encode_token(email=email)
#     activation_link = reverse('activate', kwargs={'token': token})
#     activation_url = f'http://{request.get_host()}{activation_link}'
#     message = f'Hi {user.full_name}, please click on this link to activate your account: {activation_url}'
#     send_mail(
#         'A user followed you',
#         message,
#         'douglasdanso66@gmail.com',
#         [user.email],
#         fail_silently=False,
#     )