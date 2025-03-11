from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order, OrderItem, Product, Inventory

class OrderCreateForm(forms.ModelForm):
    customer_name = forms.CharField(widget=forms.TimeInput(attrs={'class': 'form-control'}))
    destination_address = forms.CharField(widget=forms.TimeInput(attrs={'class': 'form-control'}))
    priority_level = forms.ChoiceField(
        choices=Order.priority_level_choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Order
        fields = ['customer_name', 'destination_address', 'priority_level']



class OrderUpdateForm(forms.ModelForm):
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

    class Meta:
        model = Order
        fields = ['customer_name', 'status', 'priority_level', 'destination_address']


class OrderItemCreateForm(forms.ModelForm):

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),  # Fetch all products
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(widget=forms.TimeInput(attrs={'class': 'form-control'}))

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

        # ensures the order quantity does not exceed available stock. 
        def clean_quantity(self):
            quantity = self.cleaned_data.get('quantity')
            product = self.cleaned_data.get('product')

            # Get total stock across all inventories for this product
            total_stock = sum(inv.stock for inv in product.inventories.all())

            if product and quantity > total_stock:
                raise forms.ValidationError(f"Only {total_stock} units available in stock.")

            return quantity

## from django.forms import inlineformset_factory
## Create an inline formset for OrderItem
OrderItemFormSet = forms.inlineformset_factory(Order, OrderItem, form=OrderItemCreateForm, extra=1) # gets implemented in order_create_view
OrderItemFormSetUpdate = forms.inlineformset_factory(Order, OrderItem, form=OrderItemCreateForm, extra=0, can_delete=True)  # gets implemented in order_update_view

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
       
