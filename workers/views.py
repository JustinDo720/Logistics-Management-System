from django.shortcuts import render, redirect
from .models import LMSWorker
# Default Django Registration Form 
# from django.contrib.auth.forms import UserCreationForm
from .forms import WorkerUserCreationForm, LMSWorkerUpdate
from django.http import HttpResponse
from django.contrib.messages import constants as messages
from django.contrib.auth import authenticate, login 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
# Create your views here.


def gen_temp(template_name):
    return f'registration/{template_name}'

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
        return render(request, gen_temp('signup.html'), context = {'register_form':register_form})
    elif request.method == 'POST':
        register_form = WorkerUserCreationForm(request.POST)
        if register_form.is_valid():
            register_form.save() 
            messages.success(request, 'Registered Successfully!')
            return redirect('login')
        else:
            # Handle Form Error 
            # Because we're extending from a UserCreationForm (it already handles the errors for us so we dont have to loop through register_form.errors)
            # Just re-render our signup template but we'll add in the error toast message
            messages.error(request, 'Failed to Register')
            return render(request, gen_temp('signup.html'), {'register_form': register_form})

def custom_login(request):
    # Custom Login to use Django Messages
    if request.method == 'GET':
        # Don't need our form because we'll render a custom form
        return render(request, gen_temp('login.html'))
    elif request.method == 'POST':
        username, password = request.POST['user_name'], request.POST['pass_word']
        possible_user = authenticate(username=username, password=password)
        if possible_user is not None:
            login(request, possible_user)
            # Since we have success tag as bg-success, we could use that in our class to modify how our Toast looks like
            messages.success(request, 'Login Successful')
            return redirect('logistics_app:home')
        
    # Error 
    messages.error(request, 'Failed to Login')
    return render(request,gen_temp('login.html'), context={'err': 'Incorrect Username or Password.'})

@login_required()
def profile(request, user_id):
    my_user = get_object_or_404(LMSWorker, id=user_id)
    if request.method == 'GET':
        update_form = LMSWorkerUpdate(instance=my_user)
        return render(request, gen_temp('profile.html'), context={'form': update_form, 'my_user': my_user})
    elif request.method == 'POST':
        update_form = LMSWorkerUpdate(instance=my_user, data=request.POST)
        if update_form.is_valid():
            # Checking for new password field before saving 
            if request.POST['new_password']:
                print('Update password')
                updated_profile = update_form.save(commit=False)
                # Use set_password NOT .password => Django hashes pw 
                updated_profile.set_password(update_form.cleaned_data['new_password'])
                updated_profile.save() 
            else: 
                # Just save the form as usual 
                update_form.save() 
            messages.success(request, 'Successfully Update Your Profile!')
            return redirect('workers:profile', user_id=user_id)
        else:
            # Form Errors
            curr_user = get_object_or_404(LMSWorker, id=user_id)
            messages.error(request, 'Failed To Update Your Profile!')
            return render(request, gen_temp('profile.html'), context={'form': update_form, 'my_user': curr_user})
