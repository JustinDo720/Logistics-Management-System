from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order, Product, Inventory

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

# Inventory Form 
class InventoryF(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].label = 'Select Product *'
        self.fields['location'].label = 'Location'
        self.fields['stock'].label = 'Quantity *'
        self.fields['stock_threshold'].label = 'Threshold *'

        self.fields['stock'].required = True
        self.fields['stock_threshold'].required = True
        self.fields['product'].required = True

        self.fields['stock_threshold'].help_text = '* Threshold amount will help us alert you to restock if the quantity for that product is LOW'
    class Meta: 
        model = Inventory 
        fields = [
            'product',
            'location',
            'stock',
            'stock_threshold',
        ]
        
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'id': 'productSelect', 'aria-label': 'Floating Label product select'}),
            'location': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'California', 'id': 'locationName'}),
            'stock': forms.NumberInput(attrs={'class':'form-control form-control-sm', 'placeholder': 5, 'id': 'quantityField'}),
            'stock_threshold': forms.NumberInput(attrs={'class':'form-control form-control-sm', 'placeholder': 4, 'id': 'thresholdField'})
        }

# Product Form 
class ProductF(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_name'].label = 'Product Name * '
        self.fields['category'].label = 'Category * '
        self.fields['price'].label = 'Price ($) * '

        self.fields['product_name'].required = True
        self.fields['category'].required = True
        self.fields['price'].required = True

    class Meta: 
        model = Product 
        fields = [
            'product_name',
            'category',
            'price'
        ]
        widgets = {
            'product_name': forms.TextInput(attrs={'class':'form-control form-control-sm', 'placeholder': 'Protein Bar', 'id': 'productName'}),
            'category': forms.TextInput(attrs={'class':'form-control form-control-sm', 'placeholder': 'Food', 'id': 'categoryName' }),
            'price': forms.NumberInput(attrs={'class':'form-control form-control-sm', 'placeholder': 5, 'id': 'priceField'})
        }
       
# Updating Route 
class StatusUpdate(forms.ModelForm):
    class Meta:
        model=Order
        fields= [
            'status',
            'priority_level'
        ]
        widgets={
            'status': forms.Select(attrs={'class': 'form-select', 'id': 'statusSelect', 'aria-label': 'Floating Label status select'}),
            'priority_level': forms.Select(attrs={'class': 'form-select', 'id': 'prioritySelect', 'aria-label': 'Floating Label priority select'})
        }