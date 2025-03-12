from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
# Custom LMS User Model 

class LMSWorker(AbstractUser):
    # We build these choices to use with CharField where it's an array of tuples that follow: (db_value, view_value)
    ROLE_CHOICES = [
        ('worker', 'Worker'),
        ('lm', 'Logistics Manager'),
        ('drivers', 'Drivers'),
        ('ws', 'Warehouse Staff')
    ]

    CARDS_CHOICES = [
        ('visa', 'Visa'),
        ('mc', 'Mastercard'),
        ('ae', 'American Express')
    ]

    email = models.EmailField(unique=True)
    card = models.CharField(max_length=10, choices=CARDS_CHOICES, default='visa')

    # Leaving username necessary to sign in 
    USERNAME_FIELD = 'username'
    # Necessary fields to create a superuser
    REQUIRED_FIELDS = ('email',)

    role = models.CharField(max_length= 25, choices=ROLE_CHOICES, default='worker')

    # Pip install Pillow 
    # Handle Profile Icons as default on Templates
    profile_icon = models.ImageField(upload_to='profile_icons/', null=True, blank=True)
    hired_date = models.DateTimeField(auto_now_add=True)

    # String Representation 
    def __str__(self): 
        return f'{self.username}-{self.email}'
    
    # Handling Profile Icon 
    def get_profile_icon(self):
        # All image sources need urls
        return self.profile_icon.url
    
    def get_profile_name(self):
        return self.profile_icon.name