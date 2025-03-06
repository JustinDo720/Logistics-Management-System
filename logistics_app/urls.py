from django.urls import path
from . import views

# App Name for name spacing 
app_name = 'logistics_app'  # accessible: logistics_app:path_name --> logistics_app:home 

urlpatterns = [
    path('', views.home_page, name='home'),
    path('orders/',views.order_list_view, name='order_list'),
    path('orderdetail/<int:pk>/',views.order_detail_view, name='order_detail'),

]
