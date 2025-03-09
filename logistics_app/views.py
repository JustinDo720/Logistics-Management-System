from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from .models import Order
from .forms import RoomUpdateForm, RoomCreateForm
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from workers.models import LMSWorker
from .models import Product, Inventory, Order, InventoryNotification
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Searching 
from .forms import InventoryF, ProductF
from django.contrib import messages
import folium

def gen_temp(temp_name):
    return f'logistics_app/{temp_name}' 

# Create your views here.
def home_page(request):
    return render(request, gen_temp('home.html'))

# Product & Inventory Management 
# CRUD - Product
@login_required()
def view_products(request):
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
        
        return render(request, gen_temp('product_view.html'), context=context)
    if request.method == 'POST':
        if 'product_name' in request.POST and 'category' in request.POST and 'price' in request.POST:
            # We're using the product form 
            prod_form = ProductF(data=request.POST)
            if prod_form.is_valid():
                prod_form.save()
                messages.success(request, 'Product Created Successfully!')
                return redirect('logistics_app:view_products')
            else: 
                messages.error(request, 'Failed To Create Product!')
            
            # Handling Form Errors 
            # Overriding the GET method form 
            context['prod_form'] = prod_form 
            return render(request, gen_temp('product_view.html'), context=context)
        else:
            # This means we're supposed to use the Inventory Form 
            inv_form = InventoryF(data=request.POST)
            if inv_form.is_valid():
                inv_form.save()
                messages.success(request, 'Inventory Created Successfully!')
                return redirect('logistics_app:view_products')
            else: 
                messages.error(request, 'Failed To Create Inventory!')

            # Handling Form Errors 
            # Overriding the GET method form 
            context['inv_form'] = inv_form 
            return render(request, gen_temp('product_view.html'), context=context)

@login_required()
def view_specific_product(request, sku):

    # Search Params:
    searched_loc = request.GET.get('location', '')
    searched_invStatus = request.GET.get('inv_status', '')

    prod = get_object_or_404(Product, sku=sku)
    inv = prod.inventories.all().order_by('-restock')

    if searched_loc or searched_invStatus:
        # Override the inventories with some filters 
        if searched_invStatus == 'all':
            inv = prod.inventories.filter(Q(location__icontains=searched_loc)).order_by('-restock')
        else:
            # Restock Options 
            searched_invStatus = True if searched_invStatus == 'restock' else False
            inv = prod.inventories.filter(Q(location__icontains=searched_loc) & Q(restock=searched_invStatus))
        

    context = {
        'product':prod, 
        'inventories': inv,
    }

    # Total Amount of Inventories 
    total = context['inventories'].count()
    context['total_inv'] = total
    
    # Average Quantity 
    inventories = context['inventories']
    try:
        context['average_stock'] = sum(inv.stock for inv in inventories) // total
    except ZeroDivisionError as e:
        context['average_stock'] = 0 

    # Needs to restock 
    inventory_restock = context['inventories'].filter(restock=True).count()
    context['amount_to_restock'] = inventory_restock

    # Health Check: below 30% is critial 50% is okay and above 50% is good 
    try:
        health_percentage = ((total-inventory_restock) / total) * 100
    except ZeroDivisionError as e:
        health_percentage = 0
        
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
        return render(request, gen_temp('update_specific_product.html'), {'prod_form':product_form, 'product': prod})

@login_required()
def delete_specific_product(request, sku):
    prod = get_object_or_404(Product, sku=sku)
    if request.method == 'GET':
        return render(request, gen_temp('delete_specific_product.html'), {'product':prod})
    else:
        # Posting (Confirms to delete)
        prod.delete()
        messages.error(request, 'Your product has been removed.')
        return redirect('logistics_app:view_products')

# ----- Inventory 
@login_required()
def view_inventory(request):
    # Search Method
    product_sku = request.GET.get('product_sku')
    location_search = request.GET.get('inv_location')
    quantity_search = request.GET.get('inv_quantity')
    # We could build a more dynamic search by appending Q() to our filter
    # https://stackoverflow.com/questions/55422638/is-there-a-way-to-concatenate-with-q-objects
    my_filter = Q()
    if product_sku:
        my_filter &= Q(product__sku__icontains=product_sku)
    elif location_search:
        my_filter &= Q(location__icontains=location_search)
    elif quantity_search:
        my_filter &= Q(stock=quantity_search)
    
    all_inv = Inventory.objects.all() if not my_filter else Inventory.objects.filter(my_filter)

    # Filtering the inventories that need to be restocked 
    restock_cnt = all_inv.filter(restock=True).count()
    if request.method == 'GET':
        inventory_form = InventoryF()
        # Getting all the notifications to show on Notify Me 
        user_notification = request.user.notifications.all()
        notified_inv = [notification.inventory for notification in user_notification]
        return render(request, gen_temp('inventory_view.html'), {'inventories': all_inv, 'inv_form': inventory_form, 'restock_cnt':restock_cnt, 'user_notications':notified_inv})
    else:
        # Handle POST 
        inventory_form = InventoryF(request.POST)
        if inventory_form.is_valid():
            inventory_form.save()
            messages.success(request, 'Inventory Added Successfully')
            return redirect('logistics_app:view_inventory')
        messages.error(request, 'Failed to add Inventory')
        return render(request, gen_temp('inventory_view.html'), {'inventories': all_inv, 'inv_form': inventory_form, 'restock_cnt':restock_cnt})
        

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
            messages.warning(request, 'Successfully Updated Your Inventory for this Product')
            return redirect('logistics_app:view_specific_product', sku=inv.product.sku)
        else:
            messages.error(request, 'There was an issue updating your inventory.')
        
        # Handling Form Errors
        return render(request, gen_temp('update_specific_inventory.html'), {'inv_form': inv_form, 'inv':inv})
    
@login_required
def delete_specific_inventory(request, id):
    inv = get_object_or_404(Inventory, id=id)
    if request.method == 'GET':
        return render(request, gen_temp('delete_specific_inventory.html'), context={'inventory': inv})
    elif request.method == 'POST':
        inv.delete()
        messages.error(request, 'Removed an Inventory.')
        return redirect('logistics_app:view_specific_product', sku=inv.product.sku) if inv.product.sku else redirect('logistics_app:view_products')
    messages.error(request, 'There was some issue in the backend.')
    return redirect('logistics_app:view_specific_product', sku=inv.product.sku) if inv.product.sku else redirect('logistics_app:view_products')

# Inventory Notifications 
@login_required
def notify_me(request):
    if request.method == 'POST':
        # https://stackoverflow.com/questions/48735726/how-to-get-checkbox-values-in-django-application
        # Checkbox uses getlist
        inventory_notification = request.POST.getlist('notifyInv')
        # Check if the noification already exists with the current user
        if inventory_notification:
            for inv_id in inventory_notification:
                inv_obj = get_object_or_404(Inventory, id=inv_id)
                if not InventoryNotification.objects.filter(user=request.user, inventory=inv_obj).exists():
                    # Then we'll add 
                    newNotification = InventoryNotification.objects.create(inventory=inv_obj, user=request.user)
                    newNotification.save()

            messages.success(request, f'Registered {len(inventory_notification)} notifications for this inventory.')
        messages.warning(request, f'Make sure you check "Notify Me" on the inventories you want to recieve notifications for.')
        return redirect('logistics_app:view_inventory') 

@login_required
def delete_notify_me(request):
    # For now we'll remove ALL notifications
    if request.method == 'POST':
        user_notifications = request.user.notifications.all()
        for notifi in user_notifications:
            notifi.delete()

        messages.warning(request, f'Removed all {len(user_notifications)} notifications for this inventory.')
        return redirect('logistics_app:view_inventory') 

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

def order_create_view(request):
    form = RoomCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('/orders/')  
    return render(request, 'logistics_app/order_create.html', {'form': form})


def order_update_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = RoomUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/orders/')
    else:
        form = RoomUpdateForm(instance=order)

    return render(request, 'logistics_app/order_update.html', {'form': form, 'order': order})

def order_delete_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        order.delete()
        return redirect('/orders/')
    return render(request, 'logistics_app/order_delete.html', {'order': order})


# CRUD - Routing 
def order_route_list(request):
    search_delivery_address = request.GET.get('addr')
    search_order_slug = request.GET.get('order_slug')

    # Dynamic Filter 
    query = Q() 
    if search_delivery_address:
        query &= Q(destination_address__icontains=search_delivery_address)
    elif search_order_slug:
        query &= Q(order_slug__icontains=search_order_slug)
    
    if query:
        all_orders = Order.objects.filter(query)
    else:
        all_orders = Order.objects.all()
    return render(request, gen_temp('order_route_view.html'), {'orders':all_orders})

def order_route(request, order_slug):
    my_order = get_object_or_404(Order, order_slug=order_slug)
    # Here is where we use folium to generate our map as html
    # We have a class variable for our headquarters but its in: Long/Lat format
    # For us to use Folium mpa it must be Lat/Long format  
    if my_order.route_coords:
        map = folium.Map(location=list(reversed(Order.HEADQUARTERS_COORDS)), zoom_start=14)
        # We create that Foliumn PolyLine which is based on our "route"
        # Again we have to reverse EVERY single coord in route_coords 
        folium.PolyLine(locations=[list(reversed(coord)) for coord in my_order.route_coords], color='blue').add_to(map)

        # Afterwards we must change this map to an html object for us to use on Django Templates 
        html_map = map._repr_html_()
        return render(request, gen_temp('specific_order_route.html'), {'map':html_map})