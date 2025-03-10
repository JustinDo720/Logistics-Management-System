from django.urls import path
from . import views

# App Name for name spacing 
app_name = 'logistics_app'  # accessible: logistics_app:path_name --> logistics_app:home 

urlpatterns = [
    path('', views.home_page, name='home'),
    # Inventory Management
    path('inventory/view/', views.view_inventory, name='view_inventory'),
    path('inventory/view/<slug:sku>/', views.view_specific_product, name='view_specific_product'),
    path('inventory/update/<int:id>/', views.update_specific_inventory, name='update_specific_inventory'),
    path('inventory/delete/<int:id>/', views.delete_specific_inventory, name='delete_specific_inventory'),
    # Product Management
    path('product/update/<slug:sku>/', views.update_specific_product, name='update_specific_product'),
    path('product/delete/<slug:sku>/', views.delete_specific_product, name='delete_specific_product'),

    # Order Management
    path('orders/',views.order_list_view, name='order_list'),
    path('order/create', views.order_create_view, name='order_create'),
    path('orderdetail/<int:pk>/',views.order_detail_view, name='order_detail'),
    path('order/update/<int:pk>/',views.order_update_view, name='order_update'),
    path('order/delete/<int:pk>/', views.order_delete_view, name='order_delete'),
]
