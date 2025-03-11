from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from .forms import OrderItemCreateForm, OrderItemFormSet, OrderItemFormSetUpdate, OrderUpdateForm, OrderCreateForm
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from workers.models import LMSWorker
from .models import Product, Inventory, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Searching 
from .forms import InventoryF, ProductF
from django.contrib import messages
from django.db.models import F
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum
import csv
from django.http import HttpResponse

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

@login_required
def order_create_view(request):
    if request.method == "POST":
        order_form = OrderCreateForm(request.POST)
        formset = OrderItemFormSet(request.POST)

        if order_form.is_valid() and formset.is_valid():
            order = order_form.save()

            for form in formset:
                order_item = form.save(commit=False)
                product = order_item.product

                # Find an inventory location with stock above the threshold, sorted by highest stock
                available_inventory = Inventory.objects.filter(
                    product=product, stock__gt=F('stock_threshold')  # Stock should be greater than threshold
                ).order_by('-stock').first()  # Select the inventory with the highest stock

                if available_inventory:
                    available_inventory.stock -= order_item.quantity  # Deduct stock
                    available_inventory.save()

                    order_item.order = order
                    order_item.inventory = available_inventory  # Store the inventory location
                    order_item.save()
                else:
                    # Handle out-of-stock scenario (optional)
                    messages.error(request, f"Not enough stock for {product.name} at any location.")
                    order.delete()  # Rollback order if needed
                    return redirect('logistics_app:order_create')

            return redirect('/orders/')

    else:
        order_form = OrderCreateForm()
        formset = OrderItemFormSet()

    return render(request, 'logistics_app/order_create.html', {
        'order_form': order_form,
        'formset': formset,
    })


 
    # order_form = OrderItemFormSetUpdate(instance=order)
    # formset = OrderItemFormSetUpdate(queryset=OrderItem.objects.filter(order=order))  # Load existing order items

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
