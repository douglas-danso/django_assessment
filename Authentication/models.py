from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def create_user(self, email, password=None, *args, **kwargs):
        if not email:
            raise ValueError('Email Address is Required')
        
        if not password:
            raise ValueError('Password is Required')

   
        try:
            user = self.model(
                email = self.normalize_email(email),
                
                *args,
                **kwargs
            )
        
            user.set_password(password)
            user.save()
            
            return user
        except:
               raise ValueError('An Error Occured Please Try Again')         
        

    def create_superuser(self, email, full_name,username, password=None, *args, **kwargs):
        try:
            user = self.create_user(
                    email,
                    full_name = full_name,
                    password=password,
                    username=username,
                    is_admin=True,
                    is_superuser=True,
                    is_staff=True,
                    *args,
                    **kwargs
            )
            
            return user
        except:
               raise ValueError('An Error Occured Please Try Again')  


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, null =True,blank=True,unique = True)
    full_name = models.CharField(max_length= 100)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.CharField(max_length=250,blank=True, null=True)
    bio = models.TextField(blank=True,null=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['']
   
    def __str__(self):
        return self.full_name





 

