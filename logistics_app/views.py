from django.shortcuts import render
from workers.models import LMSWorker

# Create your views here.
def home_page(request):
    return render(request, 'logistics_app/home.html')