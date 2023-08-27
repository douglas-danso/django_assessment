from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from helpers.permissions import IsAdminOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import CustomUser
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404,JsonResponse
from rest_framework.exceptions import NotFound
import jwt
from helpers.send_emails import send_activation_email
from helpers.utils import decode_token,encode_token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import cloudinary
import cloudinary.uploader


class SignUp(APIView):
    def post(self, request, *args, **kwargs):
        data=request.data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            print(user.email)
            send_activation_email(request=request, user=user)
            return Response({"detail": "You have signed up successfully. Please check your email to activate your account."},
                        status=status.HTTP_201_CREATED)    
        return Response({"detail": serializer.validate(data)}, status=status.HTTP_400_BAD_REQUEST)
        
        


class Login(APIView):
    def post(self,request,*args, **kwargs):
        username= request.data.get('username')
        password = request.data.get('password')

        try:
            user = CustomUser.objects.get(username= username)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Invalid username'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'detail': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_verified:
            send_activation_email(request=request, user=user)
            return Response({"detail":"You have not verified your account, check your email for the activation link"},status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        data = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
        user_id = encode_token(user_id=user.id)
        return Response({
            'user': UserSerializer(user).data,
            'data':data,
            'user_id': user_id
        }, status=status.HTTP_200_OK)

class ResendActivationLink(generics.GenericAPIView):
    permission_classes = ()
    serializer_class = ResendSerializer()
    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = CustomUser.objects.get(email=serializer.validated_data['email'])
        except (CustomUser.DoesNotExist):
            return Response('detail: user does not exist')
        if user.is_active == True and user.is_verified== True:
            return Response('detail: user is already verified')
        else:
            send_activation_email(request, user)
            return Response('detail: activation email sent')

class Activate(APIView):
    permission_classes = ()
    def post(self, request, token):
        try:
            decoded_token = decode_token(token)
            user_email = decoded_token['email']
            print(user_email)
            user = CustomUser.objects.get(email=user_email)
        except (jwt.exceptions.DecodeError, CustomUser.DoesNotExist):
            raise Http404('Invalid activation link')
        
        if not user.is_verified:
            user.is_verified = True
            user.is_active = True
            user.save()
            return JsonResponse({'detail': 'User has been verified'})
        else:
            return JsonResponse({'detail': 'User has already been verified'})


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    def post(self, request, format=None,*args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.get(email=serializer.validated_data['email'])
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = request.build_absolute_uri(
                 reverse('passwordresetconfirm', kwargs={'uidb64': uidb64, 'token': token}))
            # Send the reset URL to the user by email
        subject = 'Password reset'
        message = f'Use this link to reset your password: {reset_url}'
        from_email = 'douglasdanso66@gmail.com'
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        # Return a success message
        return Response({'success': 'Password reset email has been sent'}, status=status.HTTP_200_OK)
    
class PasswordResetConfirm(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        data=request.data
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
                    user = None
        serializer = self.get_serializer(data=data,context={'user':user})
        if serializer.is_valid():
            password = serializer.validated_data['password']
        
            if user is not None and default_token_generator.check_token(user, token):
                
                if  user.check_password(password):
                    return Response({'detail':'password cannot be the same as previous password.'})
                user.set_password(password)
                user.save()
                return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)

            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": serializer.validate(data)}, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordChange(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def put(self, request, *args, **kwargs):
        user = self.request.user
        data=request.data
        serializer = self.get_serializer(data=data,context={'user':user})
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            
            
            if not user.check_password(current_password):
                raise NotFound("You have entered the wrong password, try again.")
            
            password = serializer.validated_data['password']
            user.set_password(password)
            user.save()
            return Response({'detail': 'Password has been changed.'}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.validate(data)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccount(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DeleteAccountSerializer 
    def delete(self,request,*args, **kwargs):
        encoded_id =kwargs.get("id")
        user_id = decode_token(encoded_id)
        id = user_id.get('user_id')
        user = CustomUser.objects.get(id = id)
        user.delete()
        return Response({"detail":"Account deleted successfully"},status=status.HTTP_200_OK)


class ProfileImageView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user
        image_file= request.FILES.get('image_file')
        if image_file:
           try:
            cloudinary_response = cloudinary.uploader.upload(image_file)
            image = cloudinary_response['secure_url']
            user.profile_picture  = image
            user.save()
           
           except cloudinary.exceptions.Error as e:
                return Response({'detail': 'Invalid image file'}, status=status.HTTP_400_BAD_REQUEST) 
        else:
            user.profile_picture  = 'Null'
            user.save()
        user_id = encode_token(user_id=user.id)
        public_id = cloudinary_response['public_id']
        context  ={"id" : user_id,
                 "image": user.profile_picture,
                 "public_id":public_id

            }
        return Response({'profile': context, 'detail' :'success'})
    
class DeleteProfilePicture(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def delete(self,request,public_id,*args, **kwargs):
        encoded_id =kwargs.get("id")
        user_id = decode_token(encoded_id)
        id = user_id.get('user_id')
        user = request.user
        try:
            user = CustomUser.objects.get(id = id)
            user.delete()
        except CustomUser.DoesNotExist:
           return Response({"detail": "Image not found"}, status=status.HTTP_404_NOT_FOUND) 
        try:
            # Delete the file from Cloudinary
            cloudinary.uploader.destroy(public_id)
            
        except cloudinary.api.Error as e:
            return Response({"error": str(e)}, status=status)
        return Response({"detail": "File deleted successfully"}, status=status.HTTP_200_OK)

class UserLists(generics.ListAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

class LogoutView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(request):
        refresh_token = request.data.get('refresh_token')
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)



class EditUserDetails(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def update_profile_picture(self,request,user):
        image_file= request.FILES.get('profile_picture')
        if image_file:
           try:
            cloudinary_response = cloudinary.uploader.upload(image_file)
            image = cloudinary_response['secure_url']
            user.profile_picture  = image
            user.save()
            public_id = cloudinary_response['public_id']
           
           except cloudinary.exceptions.Error as e:
                return Response({'detail': 'Invalid image file'}, status=status.HTTP_400_BAD_REQUEST) 
        
        else:
            public_id = 'Null'
        context  ={
                 "image": user.profile_picture,
                 "public_id":public_id

            }
        return context
    def put(self, request, *args, **kwargs):
        encoded_id =kwargs.get("id")
        user_id = decode_token(encoded_id)
        id = user_id.get('user_id')

        user = get_object_or_404(CustomUser, id=id)
        
        if user != request.user:
            return Response({"details": "You don't have permission to edit this profile."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            profile_picture = self.update_profile_picture(request,user)
            return Response({"details": "Profile updated successfully.",
                             "user": UserProfileSerializer(user).data, 
                             "profile_picture":profile_picture}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    
