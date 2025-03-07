from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from .models import Order
from .forms import RoomUpdateForm, RoomCreateForm

# Create your views here.
def home_page(request):
    return render(request, 'logistics_app/home.html')

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