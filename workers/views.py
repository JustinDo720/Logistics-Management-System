from django.shortcuts import render, redirect
from .models import LMSWorker
# Default Django Registration Form 
# from django.contrib.auth.forms import UserCreationForm
from .forms import WorkerUserCreationForm
from django.http import HttpResponse
# Create your views here.

def register(request):
    """
        We have 2 major request method: GET & POST 

        Whenever we have a GET request we're only going to display a register form
        - Django has a built-in UserCreationForm in which we pass to display on our template via context
        - HOWEVER, since we swapped the default User model, we must make our own form in workers/forms.py 

        Within the signup.html template, there will be a form tag with an "action" directed back into this function WITH a post method

        We handle POST method by creating the same exact form with request.POST which is the data:
        - Check if the form is good to save into our db
        
        After saving to our db, we redirect our users to login
    """
    if request.method == 'GET': 
        register_form = WorkerUserCreationForm()
        return render(request, 'registration/signup.html', context = {'register_form':register_form})
    elif request.method == 'POST':
        register_form = WorkerUserCreationForm(request.POST)
        if register_form.is_valid():
            register_form.save() 
            return redirect('login')
    # Error 
    return HttpResponse('Error')