from django.urls import path,include
from .views import *
urlpatterns = [
    path('signup/', SignUp.as_view(), name='signup'),
    path('login/', Login.as_view(), name='login'),
    path('user-lists/', UserLists.as_view(), name='user_lists'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password-change/', PasswordChange.as_view(), name='password_change'),
    path('delete-account/<str:id>/', DeleteAccount.as_view(), name='delete_account'),
    path('activate/<token>/', Activate.as_view(), name='activate'),
    path('profile-image/', ProfileImageView.as_view(), name='profile_image'),
    path('user-details/edit/<id>', EditUserDetails.as_view(), name='edit-user'),
    path('resend-activation/', ResendActivationLink.as_view(), name='resend_activation'),
    path('logout/', LogoutView.as_view(), name='logout'),
]







