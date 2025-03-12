from django.urls import path
from . import views

# App Name for name spacing 
app_name = 'logistics_app'  # accessible: logistics_app:path_name --> logistics_app:home 

urlpatterns = [
    path('', views.home_page, name='home'),
    # Inventory Management
    path('inventory/view/', views.view_inventory, name='view_inventory'),
    path('inventory/update/<int:id>/', views.update_specific_inventory, name='update_specific_inventory'),
    path('inventory/delete/<int:id>/', views.delete_specific_inventory, name='delete_specific_inventory'),
    # Notifications
    path('inventory/notify/', views.notify_me, name='notify_me'),
    path('inventory/notify/remove_all/', views.delete_notify_me, name='delete_notify_me'),

    # Product Management
    path('product/view/', views.view_products, name='view_products'),
    path('product/view/<slug:sku>/', views.view_specific_product, name='view_specific_product'),
    path('product/update/<slug:sku>/', views.update_specific_product, name='update_specific_product'),
    path('product/delete/<slug:sku>/', views.delete_specific_product, name='delete_specific_product'),

    # Order Management
    path('orders/',views.order_list_view, name='order_list'),
    path('order/create', views.order_create_view, name='order_create'),
    # Continue Order creation 
    path('order/create/continue/', views.order_create_cont, name='order_create_cont'),
    path('orderdetail/<int:pk>/',views.order_detail_view, name='order_detail'),
    path('order/update/<int:pk>/',views.order_update_view, name='order_update'),
    path('order/delete/<int:pk>/', views.order_delete_view, name='order_delete'),
    # Order Item
    path('orders/create/continue/clear/', views.clear_order_create, name='clear_order_create_cont'),
    path('orders/create/success/', views.order_payment_success, name='order_create_success'),
    # Drivers Management 
    path('order/route/list/', views.order_route_list, name='order_route_list'),
    path('order/route/<slug:order_slug>/', views.order_route, name='order_route'),
    path('order/route/update/<slug:order_slug>/', views.update_order_status, name='update_order_status'),

    path('orderitem/create/', views.order_item_create_view, name='order_item_create'),

    # Report Summary
    path('reports/', views.report_summary_view, name='report_summary'),
    path('download/csv', views.download_csv_report_view, name='download_csv_report'),

]
