from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from workers.models import LMSWorker
from .models import Product, Inventory, Order
from django.contrib.auth.decorators import login_required
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
@login_required()
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

@login_required()
def view_specific_product(request, sku):
    prod = get_object_or_404(Product, sku=sku)
    context = {
        'product':prod, 
        'inventories': prod.inventories.all().order_by('-restock'),
    }

    # Total Amount of Inventories 
    total = context['inventories'].count()
    context['total_inv'] = total
    
    # Average Quantity 
    inventories = context['inventories']
    context['average_stock'] = sum(inv.stock for inv in inventories) // total

    # Needs to restock 
    inventory_restock = prod.inventories.filter(restock=True).count()
    context['amount_to_restock'] = inventory_restock

    # Health Check: below 30% is critial 50% is okay and above 50% is good 
    health_percentage = ((total-inventory_restock) / total) * 100
    if health_percentage <= 30:
        context['health_check'] = 'CRITICAL'
    elif health_percentage > 30 and health_percentage <= 50:
        context['health_check'] = 'OK'
    else:
        context['health_check'] = 'HEALTHY'

    return render(request, gen_temp('specific_product.html'), context)

@login_required()
def update_specific_product(request, sku):
    prod = get_object_or_404(Product, sku=sku)
    if request.method == 'GET':
        product_form = ProductF(instance=prod)
        return render(request, gen_temp('update_specific_product.html'), {'prod_form':product_form, 'product': prod})
    else:
        # Post Request 
        product_form = ProductF(instance=prod, data=request.POST)
        if product_form.is_valid():
            product_form.save()
            messages.warning(request, 'Successfully Updated Your Product')
            return redirect('logistics_app:view_specific_product', sku=sku)
        else:
            messages.error(request, 'There was an issue updating your product')
        
        # Handling Form Errors
        render(request, gen_temp('update_specific_product.html'), {'prod_form':product_form, 'product': prod})

@login_required()
def delete_specific_product(request, sku):
    prod = get_object_or_404(Product, sku=sku)
    if request.method == 'GET':
        return render(request, gen_temp('delete_specific_product.html'), {'product':prod})
    else:
        # Posting (Confirms to delete)
        prod.delete()
        messages.error(request, 'Your product has been removed.')
        return redirect('logistics_app:view_inventory')
    
@login_required()
def update_specific_inventory(request, id):
    inv = get_object_or_404(Inventory, id=id)
    if request.method == 'GET':
        inv_form = InventoryF(instance=inv)
        return render(request, gen_temp('update_specific_inventory.html'), {'inv_form': inv_form, 'inv':inv})
    else:
        # Post Request 
        inv_form = InventoryF(instance=inv, data=request.POST)
        if inv_form.is_valid():
            inv_form.save()
            messages.warning(request, 'Successfully Updated Your Iventory for this Product')
            return redirect('logistics_app:view_specific_product', sku=inv.product.sku)
        else:
            messages.error(request, 'There was an issue updating your inventory.')
        
        # Handling Form Errors
        return render(request, gen_temp('update_specific_inventory.html'), {'inv_form': inv_form, 'inv':inv})
    
@login_required
def delete_specific_inventory(request, id):
    inv = get_object_or_404(Inventory, id=id)
    if request.method == 'POST':
        inv.delete()
        messages.error(request, 'Removed an Inventory.')
        return redirect('logistics_app:view_specific_product', sku=inv.product.sku)
    messages.error(request, 'There was some issue in the backend.')
    return redirect('logistics_app:view_specific_product', sku=inv.product.sku)

# CRUD - Orders
def order_list_view(request):
    query = request.GET.get('query', '')
    if query:
        orders = Order.objects.filter(customer_name__icontains=query)   # case insensitive search
    else:
        orders = Order.objects.all()    # show all orders if no search term

    return render(request, 'logistics_app/order_list.html', {'orders': orders})

def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'logistics_app/order_detail.html', {'order': order})
