from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=False,  # Allow duplicate usernames
        help_text='Optional. 150 characters or fewer.',
        validators=[],  # Remove default ASCII/alphanumeric restrictions
    )
    phone_number = models.CharField(max_length=20,blank=True,null=True)
    profile_photo = models.ImageField(upload_to="profile/",blank=True,null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Crm(models.Model):
    full_name = models.CharField(max_length=255,blank=True,null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="crms") 
    email_address = models.CharField(max_length=255,blank=True,null=True)
    phone_number = models.CharField(max_length=255,blank=True,null=True)
    price = models.CharField(max_length=255,blank=True,null=True)
    event_type = models.CharField(max_length=255,blank=True,null=True)        

        
