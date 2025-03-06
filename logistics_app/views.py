from django.urls import reverse_lazy
from django.shortcuts import render, redirect 
from workers.models import LMSWorker
from .models import Product, Inventory
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q  # Searching 
from .forms import InventoryF, ProductF
from django.contrib import messages

def gen_temp(temp_name):
    return f'logistics_app/{temp_name}' 

# Create your views here.
def home_page(request):
    return render(request, gen_temp('home.html'))


# Product & Inventory Management 
# CRUD - Inventory 
def view_inventory(request):
    """
        This view could serve three purposes:
            1) Searching via GET request (with url params) because we could catch that url param value 
            2) Listing via GET request all of our products + inventory 
            3) Modal to create Inventory|Product 

        We always build our product + inventory object to display on our tables 

        Depdnding on GET or POST we'll render / handle that specific form 
        We're also sending Toast messages as well as handling/showing form errors 
    """

    # Generating our create forms 
    inv_form = InventoryF()
    prod_form = ProductF()

    # Using the get() function helps us against the edge case in which product_sku doesn't exist
    product_sku = request.GET.get('product_sku')
    # The idea is that we could experiment showing Products + Their inventories
    prod_and_inv = []
    if Product.objects.count():
        # If there's a product_sku, we filter our Product moodel for anything that contains our product_sku
        all_products = Product.objects.all() if not product_sku else Product.objects.filter(Q(sku__icontains=product_sku))

        for prod in all_products:
            prod_inv_obj = {
                'product': prod, 
                'inventories': prod.inventories.all().order_by('-restock')
            }
            prod_and_inv.append(prod_inv_obj)

    context = {
        'inv_form': inv_form,
        'prod_form': prod_form,
        'prod_info': prod_and_inv
    }

    if request.method == 'GET':
        context['inv_form'] = inv_form 
        context['prod_form'] = prod_form 
        
        return render(request, gen_temp('inventory_view.html'), context=context)
    if request.method == 'POST':
        if 'product_name' in request.POST and 'category' in request.POST and 'price' in request.POST:
            # We're using the product form 
            prod_form = ProductF(data=request.POST)
            if prod_form.is_valid():
                prod_form.save()
                messages.success(request, 'Product Created Successfully!')
                return redirect('logistics_app:view_inventory')
            else: 
                messages.error(request, 'Failed To Create Product!')
            
            # Handling Form Errors 
            # Overriding the GET method form 
            context['prod_form'] = prod_form 
            return render(request, gen_temp('inventory_view.html'), context=context)
        else:
            # This means we're supposed to use the Inventory Form 
            inv_form = InventoryF(data=request.POST)
            if inv_form.is_valid():
                inv_form.save()
                messages.success(request, 'Inventory Created Successfully!')
                return redirect('logistics_app:view_inventory')
            else: 
                messages.error(request, 'Failed To Create Inventory!')

            # Handling Form Errors 
            # Overriding the GET method form 
            context['inv_form'] = inv_form 
            return render(request, gen_temp('inventory_view.html'), context=context)

