from django.urls import path
from . import views

# App Name for name spacing 
app_name = 'workers'  # accessible: workers:path_name --> workers:register 

urlpatterns = [
    path('accounts/register/', views.register, name='register')
]
