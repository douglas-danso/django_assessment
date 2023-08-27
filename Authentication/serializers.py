from rest_framework import serializers
from .models import CustomUser
from helpers.validator import CustomPasswordValidator,validate_input
from rest_framework.response import Response
from rest_framework import status
from .models import Privacy

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'full_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        validation_response = validate_input(email.lower(), full_name)
        if validation_response:
            raise serializers.ValidationError(validation_response,status.HTTP_400_BAD_REQUEST)
        validator = CustomPasswordValidator()
        validator.validate(password)
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({'detail': 'User with this email already exists.'})
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({'detail': 'User with this username already exists.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user

    

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, data):
        # Check if the email is associated with a registered user
        user = CustomUser.objects.filter(email=data).first()
        if not user:
            raise serializers.ValidationError("No account is associated with this email.")
        return data
    
class PasswordResetConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("password","confirm_password")
    # password = serializers.CharField(
    #     write_only=True,
    #     required=True,
    #     # validators=[CustomPasswordValidator()]
    # )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True
    )
    
    def validate(self,data):
        user = self.context.get('user')
        
        password = data['password']

        validator = CustomPasswordValidator()
        validator.validate(password)
        
        if user.check_password(password):
            raise serializers.ValidationError({'detail':'New password cannot be the same as the old password.'})
        
        """
        Check that the two password fields match
        """
        if password != data['confirm_password']:
            raise serializers.ValidationError({"detail":"Passwords do not match"})
        return data
    
class PasswordChangeSerializer(PasswordResetConfirmSerializer):
    current_password = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta(PasswordResetConfirmSerializer.Meta):
        fields = ('current_password', 'password', 'confirm_password')
    def password_check(self,data):
        user = self.context.get('user')
        current_password = data['current_password']
        if not user.check_password(current_password):
            raise serializers.ValidationError('you have entered the wrong password check and try again.')
        
class DeleteAccountSerializer(PasswordResetSerializer):
    def get_user(self,email):
        user = CustomUser.objects.get(email=email)
        return user

class ResendSerializer(PasswordResetSerializer):
    pass

class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'bio','profile_privacy']

    full_name = serializers.CharField(required=False) 



    def update(self, instance, validated_data):
        bio = validated_data.get('bio')
        full_name= validated_data.get('full_name')
        profile_privacy = validated_data.get('profile_privacy',Privacy.default_choice)
        if bio:
            instance.bio = bio
        if full_name:
            instance.full_name = full_name
        if profile_privacy:
            valid_privacy_choices = [choice[0] for choice in Privacy.privacy_choices]
            if profile_privacy not in valid_privacy_choices:
                return Response({"detail": f"Invalid choice. Allowed values: {', '.join(valid_privacy_choices)}"}, status=status.HTTP_400_BAD_REQUEST)
            instance.profile_privacy = profile_privacy
        instance.save()
        return instance