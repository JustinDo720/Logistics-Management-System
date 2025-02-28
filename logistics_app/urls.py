from django.urls import path
from . import views

# App Name for name spacing 
app_name = 'logistics_app'  # accessible: logistics_app:path_name --> logistics_app:home 

urlpatterns = [
    path('', views.home_page, name='home')
]
