from django.http import JsonResponse
from workers.models import LMSWorker
from .models import Product, Inventory, Order, InventoryNotification, Route, OrderStatusHistory, OrderItem
from .forms import OrderItemCreateForm, OrderItemFormSet, OrderItemFormSetUpdate, OrderUpdateForm, OrderCreateForm, InventoryF, ProductF, StatusUpdate
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Searching 
from django.contrib import messages
import folium
from django.db.models import F
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum
import csv
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import stripe
import json

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
@login_required
def order_list_view(request):
    query = request.GET.get('query', '')
    if query:
        orders = Order.objects.filter(customer_name__icontains=query)   # case insensitive search
    else:
        orders = Order.objects.all()    # show all orders if no search term

    return render(request, 'logistics_app/order_list.html', {'orders': orders})

@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'logistics_app/order_detail.html', {'order': order, 'order_items': order_items})

# CRUD - Order Items | Creating an Order With multiple Order Items 
# Helper Function
def clear_session(request):
    if 'temp_total_price' in request.session:
        del request.session['temp_total_price']

    if 'temp_order_items' in request.session:
        del request.session['temp_order_items']

    if 'user_temp_order' in request.session:
        del request.session['user_temp_order']

    return True 

@login_required
def order_create_view(request):
    """
        The idea is that we CONTINUE our form to select multiple Products 

        For each product we create an Order Item Object 

        Finally we tie all order itms into that one order 

    """
    if request.method == "POST":

        order_form = OrderCreateForm(request.POST)
        # formset = OrderItemFormSet(request.POST)

        if order_form.is_valid():
            order_form.save(commit=False)
            # This is where we use DJango Sessions to access accross views
            # The idea is that we don't save UNTIL the user pays 
            # Make sure to pass in the form NOT the order itself
            request.session['user_temp_order'] = order_form.cleaned_data    # Because the order instance is not a serializable item to pass in sessions  

            # We'll save the order first and then redirect to another view to continue our order creation 
            # Since we're using sesions, we don't need a pk
            return redirect('logistics_app:order_create_cont')

    else:
        order_form = OrderCreateForm()
        # Before we create, we should ALWAYS get rid of our django sessions
        clear_session(request)

    return render(request, 'logistics_app/order_create.html', {
        'order_form': order_form
    })

@login_required
def order_create_cont(request):
    # We'll use django sessions to retrieve our temp order 
    # Remember our Django Session holds form data so we could reconstruct our order object
    order_data = request.session.get('user_temp_order', None)
    # https://stackoverflow.com/questions/1571570/can-a-dictionary-be-passed-to-django-models-on-create
    # order = Order.objects.create(id=order_data.id, customer_name=order_data.customer_name, 
    #                              order_slug=order_data.customer_name, date=order_data.date, status=order_data.status,
    #                              priority_level=order_data.priority_level, destination_address=order_data.destination_address)
    order = Order(**order_data)  # Passes in key,value similar to what we commented out above (But this doesnt CREATE our order object just fills in the data)
    # Catching our Order Items Params
    oi_sku = request.GET.get('product')
    oi_quantity = request.GET.get('quantity')

    # Display a form to choose a bunch of products first 
    if request.method == 'GET' and order:
        all_products = Product.objects.all()
        formset = OrderItemCreateForm()
        # Displaying a list of Order Items for this Order 
        # Django Session Temp Order Item
        temp_oi_list = request.session.get('temp_order_items', [])
        temp_total_price = request.session.get('temp_total_price',0)
        # We'll save our items if the user submitted a product + quantity 
        if oi_sku and oi_quantity:
            product = get_object_or_404(Product, sku=oi_sku)
            # Since we're working with temp data, we don't need to create an OrderItem object
            # We just need to pass the chosen product along with the quantity 
            # After payment we'll take care of saving the order, then create the orderitem 
            temp_oi = {
                'product_sku': product.sku,
                'quantity': oi_quantity,
                'product_name': product.product_name,
                'price': float(product.price)
            }
            
            # Adding this to our list of order item
            temp_oi_list = request.session.get('temp_order_items', [])
            temp_oi_list.append(temp_oi)

            # Saving to our session 
            request.session['temp_order_items'] = temp_oi_list
            print('New: ', request.session.get('temp_order_items', []))

            # Manually Calculating the total price for this temp order item list 
            temp_total_price += int(oi_quantity) * float(product.price)
            request.session['temp_total_price'] = float(temp_total_price)   # Sooo weird, Decimal isnt JSON Serializable, but they accept float 

            print(request.session['temp_total_price'])

        return render(request, gen_temp('order_create_confirm.html'), {'all_products':all_products, 'oi_form': formset, 'curr_oi': temp_oi_list, 'total_price':temp_total_price})

def clear_order_create(request):
    # Since the data is temp, we just need to clear our Django Session
    finished_clear = clear_session(request)
    if finished_clear:
        messages.warning(request, 'Cleared Previous Order Data')
    return redirect('logistics_app:order_list')

@login_required
def order_payment_success(request):
    # Handling success (This is where we build our order object)
    order_fd = request.session.get('user_temp_order', None)
    order_oi_fd = request.session.get('temp_order_items', None)
    
    if order_fd and order_oi_fd:
        # Build our actual order 
        order = Order.objects.create(**order_fd)
        order.save() 

        # All the order items:
        for o_item in order_oi_fd:
            print(o_item)
            # o_item has: product_sku & quantity which are fields we need to build order_item 
            product = get_object_or_404(Product, sku=o_item['product_sku'])
            order_item = OrderItem.objects.create(order=order, product=product, quantity=o_item['quantity'])
            order_item.save()

            # Handling Inventory deducation
            # Find an inventory location with stock above the threshold, sorted by highest stock
            available_inventory = Inventory.objects.filter(
                product=product, stock__gt=F('stock_threshold')  # Stock should be greater than threshold
            ).order_by('-stock').first()  # Select the inventory with the highest stock
         
            if available_inventory:
                available_inventory.stock -= int(order_item.quantity)  # Deduct stock
                available_inventory.save()

                order_item.order = order
                order_item.inventory = available_inventory  # Store the inventory location
                order_item.save()
            else:
                # Handle out-of-stock scenario (optional)
                messages.warning(request, f"Low stock for {product.product_name} at any location.")
                # order.delete()  # Rollback order if needed
                # return redirect('logistics_app:order_create_cont', pk=order.id)
        
        # Finished Building Order with associated Order Item + Deducting from highest Inventory
        messages.success(request, 'Successfully Created Order. An email has been sent for confirmation!')

        # Sending Confirmation Email:
        success_html_msg = render_to_string(gen_temp('emails/order_success.html'), {'order_details': order})
        send_mail(
            'Thank you for your purchase with LMS!',
            success_html_msg,
            settings.EMAIL_HOST_USER,
            [order.customer_email],
            fail_silently=False,
        )

        # Clean Django Session (Temp Keys)
        clear_session(request)
        return redirect('logistics_app:order_list')
        

@login_required
def order_update_view(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        order_form = OrderUpdateForm(request.POST, instance=order)
        formset = OrderItemFormSetUpdate(request.POST, instance=order)

        if order_form.is_valid() and formset.is_valid():
            order_form.save()

            for form in formset:
                order_item = form.save(commit=False)

                if form.cleaned_data.get('DELETE'):
                    # Restore stock in the **same inventory location** used in the order
                    if order_item.inventory:
                        order_item.inventory.stock += order_item.quantity
                        order_item.inventory.save()
                    
                    order_item.delete()
                else:
                    if order_item.pk:  # Updating existing item
                        old_order_item = OrderItem.objects.get(pk=order_item.pk)
                        stock_adjustment = old_order_item.quantity - order_item.quantity

                        # Adjust stock in the same inventory location
                        if order_item.inventory:
                            order_item.inventory.stock += stock_adjustment
                            order_item.inventory.save()
                    else:  # Creating a new order item
                        available_inventory = Inventory.objects.filter(
                            product=order_item.product, stock__gte=order_item.quantity
                        ).first()
                        
                        if available_inventory:
                            available_inventory.stock -= order_item.quantity
                            available_inventory.save()
                            order_item.inventory = available_inventory  # Store the correct inventory location

                    order_item.save()

            return redirect('/orders/')
    
    else:
        order_form = OrderUpdateForm(instance=order)
        formset = OrderItemFormSetUpdate(instance=order)

    return render(request, 'logistics_app/order_update.html', {
        'order_form': order_form,
        'formset': formset,
        'order': order
    })


@login_required
def order_delete_view(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        # Restore inventory stock before deleting the order
        for order_item in order.order_items.all():
            inventory = order_item.inventory  # Retrieve the specific inventory location
            
            if inventory:
                inventory.stock += order_item.quantity  # Restore stock
                inventory.save()

        order.delete()  # Now delete the order after restoring inventory
        return redirect('/orders/')

    return render(request, 'logistics_app/order_delete.html', {'order': order})

# CRUD - Routing 
@login_required
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

@login_required
def order_route(request, order_slug):
    my_order = get_object_or_404(Order, order_slug=order_slug)
    my_route_history = my_order.status_history.all().order_by('-last_updated')
    if request.method == 'GET':
        # Here is where we use folium to generate our map as html
        # We have a class variable for our headquarters but its in: Long/Lat format
        # For us to use Folium mpa it must be Lat/Long format  
        # Our order instance is a One-to-One relationship with Route so we could do my_order.route
        if my_order.route.route_coords:
            map = folium.Map(location=list(reversed(Order.HEADQUARTERS_COORDS)), zoom_start=14)
            # We create that Foliumn PolyLine which is based on our "route"
            # Again we have to reverse EVERY single coord in route_coords 
            folium.PolyLine(locations=[list(reversed(coord)) for coord in my_order.route.route_coords], color='blue').add_to(map)

            # Afterwards we must change this map to an html object for us to use on Django Templates 
            html_map = map._repr_html_()
            return render(request, gen_temp('specific_order_route.html'), {'map':html_map, 'order':my_order, 'shipping_history': my_route_history})
    elif request.method == 'POST':
        # Regenerating the route 
        my_order.route.build_route()
        my_order.route.save() 
        messages.warning(request, 'Attempting to update the route path...')
        return redirect('logistics_app:order_route', order_slug=order_slug)
    
@login_required
def update_order_status(request, order_slug):
    # StatusUpdate
    my_order = get_object_or_404(Order, order_slug=order_slug)
    if request.method == 'GET':
        update_form = StatusUpdate(instance=my_order)
        return render(request, gen_temp('update_order_status.html'), {'update_form':update_form, 'order': my_order})
    else:
        update_form = StatusUpdate(instance=my_order, data=request.POST)
        if update_form.is_valid():
            update_form.save() 
            messages.success(request, 'We changed the Status of an Order')
            return redirect('logistics_app:order_route', order_slug=order_slug) 
        messages.error(request, 'We failed to change the status of an order.')
        # Handling form error 
        return render(request, gen_temp('update_order_status.html'), {'update_form':update_form, 'order': my_order})

def order_item_create_view(request):
    form = OrderItemCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('/orders/')
    return render(request, 'logistics_app/order_item_create.html', {'form': form})


## view to show reports

def report_summary_view(request):
    # Get filter values from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    priority_level = request.GET.get('priority_level')

    # Filter orders based on user input
    orders = Order.objects.all()

    if start_date:
        orders = orders.filter(date__gte=start_date)
    if end_date:
        orders = orders.filter(date__lte=end_date)
    if status and status != "All":
        orders = orders.filter(status=status)
    if priority_level and priority_level != "All":
        orders = orders.filter(priority_level=priority_level)

    # Group orders by month
    orders_by_month = (
        orders.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total_orders=Count('id'))
        .order_by('month')
    )

    # Get inventory stock summary
    inventory_data = Inventory.objects.values('product__product_name').annotate(total_stock=Sum('stock'))

    # Prepare data for Chart.js
    order_labels = [entry['month'].strftime('%b %Y') for entry in orders_by_month]
    order_data = [entry['total_orders'] for entry in orders_by_month]

    inventory_labels = [entry['product__product_name'] for entry in inventory_data]
    inventory_stock = [entry['total_stock'] for entry in inventory_data]

    context = {
        'order_labels': order_labels,
        'order_data': order_data,
        'inventory_labels': inventory_labels,
        'inventory_stock': inventory_stock,
        'start_date': start_date,
        'end_date': end_date,
        'selected_status': status,
        'selected_priority': priority_level,
        'statuses': ['All'] + [choice[0] for choice in Order.status_choices],
        'priority_levels': ['All'] + [choice[0] for choice in Order.priority_level_choices],
    }
    return render(request, 'logistics_app/report_summary.html', context)


def download_csv_report_view(request):
    # Get filter parameters from the GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Apply filtering based on user input
    if start_date and end_date:
        orders = Order.objects.filter(date__range=[start_date, end_date])
    else:
        orders = Order.objects.all()  # No filter, get all orders

    # Create an HTTP response with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow(['Order ID', 'Customer Name', 'Date', 'Status', 'Total Price'])

    # Write data rows
    for order in orders:
        writer.writerow([order.id, order.customer_name, order.date, order.status, order.total_price])

    return response

# Stripe Payment Gateway 
stripe.api_key = settings.STRIPE_SECRET_KEY

def handle_payment(request):
    # Remember we're using Django Sessions which hasn't been cleared yet
    # https://stackoverflow.com/questions/74100476/integrate-stripe-payment-flow-into-django
    # PaymentIntent
    total_amount = request.session.get('temp_total_price', 0)   
    stripe_amt = int(total_amount * 100)    # This must be in cents for stripe 
    if request.method == "POST":
        intent = stripe.PaymentIntent.create(
            amount=stripe_amt,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        # return HttpResponse(
        #     json.dumps({'clientSecret': intent['client_secret']}),
        #     content_type='application/json'
        # )
        return JsonResponse({'clientSecret': intent['client_secret']})
    else:
        # Building the payment form
        curr_oi = request.session.get('temp_order_items', None)   
        return render(request, gen_temp('stripe/checkout.html'), {'curr_oi':curr_oi, 'total_price':total_amount})