from django import forms 
from django.contrib.auth.forms import UserCreationForm
from .models import LMSWorker

# We need to create our own UserCreationForm because we have a custom User model
class WorkerUserCreationForm(UserCreationForm):

    class Meta:
        model = LMSWorker
        fields = [
            'username',
            'email'
        ]