# Import necessary modules and classes
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from helpers.utils import delete_cloudinary_file
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import CustomUser
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404, JsonResponse
from rest_framework.exceptions import NotFound
import jwt
from helpers.send_emails import send_activation_email
from helpers.utils import decode_token, encode_token
from rest_framework_simplejwt.exceptions import TokenError
import cloudinary
import cloudinary.uploader
from .tasks import *
from tempfile import NamedTemporaryFile

# Define the SignUp view for user registration
class SignUp(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from request
        data = request.data
        # Serialize and validate user data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            # Save user and trigger account activation
            user = serializer.save()

            # Prepare data for Celery task and send activation email
            request_data = {'host': request.get_host()}
            user_data = {'email': user.email, 'full_name': user.full_name}
            try:
                send_activation_email_async.apply_async(args=[request_data, user_data])
            except:
                send_activation_email(request=request, user=user)

            # Return success response
            return Response({"detail": "You have signed up successfully. Please check your email to activate your account."},
                            status=status.HTTP_201_CREATED)
        # Return error response with validation errors
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# Define the Login view for user login
class Login(APIView):
    def post(self, request, *args, **kwargs):
        # Extract username and password from request data
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            # Retrieve user based on username
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Invalid username'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if provided password matches user's password
        if not user.check_password(password):
            return Response({'detail': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
        # Check if user is verified
        if not user.is_verified:
            send_activation_email(request=request, user=user)
            return Response({"detail": "You have not verified your account, check your email for the activation link"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Generate JWT tokens for authentication
        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }
        user_id = encode_token(user_id=user.id)
        # Return user data and tokens in the response
        return Response({
            'user': UserSerializer(user).data,
            'data': data,
            'user_id': user_id
        }, status=status.HTTP_200_OK)
        
# Define the ResendActivationLink view for resending activation emails
class ResendActivationLink(generics.GenericAPIView):
    permission_classes = ()
    serializer_class = ResendSerializer()

    def post(self, request):
        # Serialize and validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Retrieve user based on email
            user = CustomUser.objects.get(email=serializer.validated_data['email'])
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User does not exist'})
        
        # Check user verification status and resend activation email if needed
        if user.is_active == True and user.is_verified == True:
            return Response({'detail': 'User is already verified'})
        else:
            request_data = {'host': request.get_host()}
            user_data = {'email': user.email, 'full_name': user.full_name}
            try:
                send_activation_email_async.apply_async(args=[request_data, user_data])
            except:
                send_activation_email(request=request, user=user)
            return Response({'detail': 'Activation email sent'})

# Define the Activate view for activating user accounts
class Activate(APIView):
    permission_classes = ()

    def post(self, request, token):
        try:
            # Decode and extract user email from token
            decoded_token = decode_token(token)
            user_email = decoded_token['email']
            
            # Retrieve user based on email
            user = CustomUser.objects.get(email=user_email)
        except (jwt.exceptions.DecodeError, CustomUser.DoesNotExist):
            raise Http404('Invalid activation link')
        
        # Check if user is already verified and activate the account
        if not user.is_verified:
            user.is_verified = True
            user.is_active = True
            user.save()
            return JsonResponse({'detail': 'User has been verified'})
        else:
            return JsonResponse({'detail': 'User has already been verified'})



# Define the PasswordResetView for initiating the password reset process
class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, format=None, *args, **kwargs):
        # Serialize and validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Retrieve user based on provided email
        user = CustomUser.objects.get(email=serializer.validated_data['email'])
        
        # Prepare data for password reset email and trigger the email
        request_data = {'base_url': request.build_absolute_uri('/')}
        user_data = {'email': user.email, 'full_name': user.full_name}
        send_passwordreset_email_async.apply_async(args=[request_data['base_url'], user_data])
        
        # Return success response
        return Response({'success': 'Password reset email has been sent'}, status=status.HTTP_200_OK)

# Define the PasswordResetConfirm view for confirming password reset
class PasswordResetConfirm(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        data = request.data
        try:
            # Decode user ID from base64 and retrieve user
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None
        
        # Validate and process password reset
        serializer = self.get_serializer(data=data, context={'user': user})
        if serializer.is_valid():
            password = serializer.validated_data['password']
            
            if user is not None and default_token_generator.check_token(user, token):
                if user.check_password(password):
                    return Response({'detail': 'Password cannot be the same as the previous password.'})
                user.set_password(password)
                user.save()
                return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)
            
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": serializer.validate(data)}, status=status.HTTP_400_BAD_REQUEST)

# Define the PasswordChange view for changing the user's password
class PasswordChange(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def put(self, request, *args, **kwargs):
        # Get user from authenticated request
        user = self.request.user
        data = request.data
        serializer = self.get_serializer(data=data, context={'user': user})
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            
            # Check if current password matches the user's password
            if not user.check_password(current_password):
                raise NotFound("You have entered the wrong password, try again.")
            
            # Update the password and return success response
            password = serializer.validated_data['password']
            user.set_password(password)
            user.save()
            return Response({'detail': 'Password has been changed.'}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.validate(data)}, status=status.HTTP_400_BAD_REQUEST)

# Define the DeleteAccount view for deleting user accounts
class DeleteAccount(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DeleteAccountSerializer 

    def delete(self, request, *args, **kwargs):
        # Decode user ID and retrieve user
        encoded_id = kwargs.get("id")
        user_id = decode_token(encoded_id)
        id = user_id.get('user_id')
        user = get_object_or_404(CustomUser, id=id)
        
        # Delete user's profile picture and the user
        file_url = user.profile_picture
        delete_cloudinary_file_async.delay(file_url)
        user.delete()
        
        return Response({"detail": "Account deleted successfully"}, status=status.HTTP_200_OK)

# Define the ProfileImageView for uploading user profile pictures
class ProfileImageView(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        image_file = request.FILES.get('profile_picture')

        if image_file:
            if image_file.content_type.startswith('image'):
                # Delete previous profile picture and upload new one asynchronously
                file_url = user.profile_picture
                delete_cloudinary_file_async.delay(file_url)
                resource_type = 'image'
                with NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                async_upload_profile.delay(temp_file_path, user.id, resource_type)
        else:
            user.profile_picture = 'Null'
            user.save()
   
        return Response({'detail': 'Successfully uploaded profile'})

# Define the DeleteProfilePicture view for deleting user profile pictures
class DeleteProfilePicture(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        encoded_id = kwargs.get("id")
        user_id = decode_token(encoded_id)
        id = user_id.get('user_id')
        user = request.user
        try:
            user = CustomUser.objects.get(id=id)
            user.delete()
        except CustomUser.DoesNotExist:
            return Response({"detail": "Image not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete user's profile picture and the user
        file_url = user.profile_picture
        delete_cloudinary_file_async.delay(file_url)
        
        return Response({"detail": "File deleted successfully"}, status=status.HTTP_200_OK)

# Define the UserLists view for listing all users
class UserLists(generics.ListAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

# Define the LogoutView for user logout
class LogoutView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        try:
            # Blacklist the refresh token to log out the user
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
    

# Define the EditUserDetails view for editing user profile details
class EditUserDetails(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def update_profile_picture(self, request, user):
        # Update user's profile picture asynchronously
        image_file = request.FILES.get('profile_picture')
        if image_file:
            if image_file.content_type.startswith('image'):
                file_url = user.profile_picture
                delete_cloudinary_file_async.delay(file_url)
                resource_type = 'image'
                 # Save the uploaded file temporarily
                with NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                async_upload_profile.delay(temp_file_path, user.id,resource_type)
        return 

    def put(self, request, *args, **kwargs):
        encoded_id = kwargs.get("id")
        user_id = decode_token(encoded_id)
        id = user_id.get('user_id')

        # Retrieve user to edit
        user = get_object_or_404(CustomUser, id=id)
        
        # Check if the authenticated user is authorized to edit the profile
        if user != request.user:
            return Response({"details": "You don't have permission to edit this profile."},
                            status=status.HTTP_403_FORBIDDEN)
        
        # Serialize and validate updated user profile data
        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Update the profile picture if provided
            self.update_profile_picture(request, user)
            return Response({"details": "Profile updated successfully."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





    
