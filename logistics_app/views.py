from django.shortcuts import render, get_object_or_404
from .models import Order

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