from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order

class RoomCreateForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TimeInput(attrs={'class': 'form-control'}))
    status = forms.ChoiceField(
        choices=Order.status_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority_level = forms.ChoiceField(
        choices=Order.priority_level_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destination_address = forms.CharField(widget=forms.TimeInput(attrs={'class': 'form-control'}))
    total_price = forms.DecimalField(widget=forms.TimeInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Order
        fields = ['customer_name', 'status', 'priority_level', 'destination_address', 'total_price']



class RoomUpdateForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TimeInput(attrs={'class': 'form-control'}))
    status = forms.ChoiceField(
        choices=Order.status_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority_level = forms.ChoiceField(
        choices=Order.priority_level_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destination_address = forms.CharField(widget=forms.TimeInput(attrs={'class': 'form-control'}))
    total_price = forms.DecimalField(widget=forms.TimeInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Order
        fields = ['customer_name', 'status', 'priority_level', 'destination_address', 'total_price']