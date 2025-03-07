from django import forms 
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from .models import LMSWorker

# We need to create our own UserCreationForm because we have a custom User model
class WorkerUserCreationForm(UserCreationForm): 
    class Meta:
        model = LMSWorker
        fields = [
            'username',
            'email'
        ]

# Need a model form of our users to update 
class LMSWorkerUpdate(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Updating some help text
        # https://stackoverflow.com/questions/24344981/how-to-change-help-text-of-a-django-form-field

        self.fields['new_password'].help_text = 'Update your password by creating a new one.'
        self.fields['username'].help_text = 'NOTE: Changing this field will change your login information.' 
        self.fields['role'].help_text = '"Worker" role is set by default.'

        # Updating required fields 
        # https://stackoverflow.com/questions/16205908/django-modelform-not-required-field
        self.fields['username'].required = False 
        self.fields['email'].required = False 
        self.fields['new_password'].required = False 


    # We're not displaying their hashed password but a fresh new password field
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=LMSWorker.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = LMSWorker
        fields = [
            'username',
            'email',
            'new_password',
            'profile_icon',
            'role'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_icon': forms.FileInput(attrs={'class': 'form-control'})
        }
