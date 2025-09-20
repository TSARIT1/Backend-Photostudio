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
    role = models.CharField(max_length=20,blank=True,null=True)
    location = models.CharField(max_length=20,blank=True,null=True)
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
    status = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.full_name


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    customer_name = models.CharField(max_length=200)
    customer_address = models.TextField()
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    prepared_by = models.CharField(max_length=100)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer_name}"


class ServiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.cost * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.quantity} x {self.cost}"




class DataStore(models.Model):
    FILE_TYPES = (
        ('photo', 'Photo'),
        ('video', 'Video'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datastore_files')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datastore/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_format = models.CharField(max_length=50)
    size = models.BigIntegerField()  # Size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Set file type based on file extension
        if not self.file_type:
            if self.file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                self.file_type = 'photo'
            elif self.file.name.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')):
                self.file_type = 'video'
        
        # Set file format from content type
        if not self.file_format:
            self.file_format = self.file.name.split('.')[-1].lower()
        
        # Set file size
        if not self.size and self.file:
            self.size = self.file.size
        
        super().save(*args, **kwargs)