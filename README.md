# Logistics Management System 

The LMS will facilitate order processing, shipment tracking, inventory management, and reporting for logistics companies. It will support both web and mobile platforms.


## Features 
- User [**Authentication**](#user-authentication) and role management 
- [**Order**](#order-management) processing and tracking 
- [**Inventory**](#inventory-management) management 
- [**Route**](#route-optimzation) optimizaiton 
- Reporting and **analytics**

## LMS UML & Screen Ketches 

Our [UML](UML%20&%20Sketches/lms_uml.PNG) class diagrams will help us create our *Django Models* and we've also included an **initial** [screen ketch](UML%20&%20Sketches/lms_sketch.png) that maps out our *Django Templates* 

## LMS Flowchart & User Story 

Our [Flowchart](flowchart_&_usecase/TekBasic_-_Flowchart.jpg) and [User Story](flowchart_&_usecase/tek_basic_LMS_spreadsheet.png) helps us map out the workflow of our logistic management system 

## Update Logs 
**03/05**
- [OpenRouteServices](https://openrouteservice.org/) | [Stripe](https://stripe.com/) NO TIME => Django email 
  -  [Getting Directions](https://www.youtube.com/watch?v=xBxWuq8SR6k)
  -  MAYBE [Rout Optimization](https://youtu.be/OOCvhc0k1R4?si=UVgdZ-y9n1AZDisy)
- LowStock => Email or Message/Toast
- Forgot Password 
  - we'll use a real [reset password](https://dev.to/earthcomfy/django-reset-password-3k0l) 
  - requires an actual working email 
  - Setting up Django Emails 
    - Google acc --> Turn **on** 2 factor auth --> **app passwords**
    - add app pass + email to `.env`  
  - We inherited from `PasswordResetView` creatin an email template body, subject template txt file and success url once we send out the email
  - Inside that email, we have a link to our custom `PasswordResetConfirmView` which renders out our form that takes *new_password* and *confirm new_password* but **also** redirects us to a success page: `PasswordResetCompleteView` 
    - All of these views are `from django.contrib.auth import views as auth_views`
- View Specific Inventory based off SKU
- Update & Remove Inventory

**03/05**
- Handling Product/Inventory Signal 
- Update Total Price Signal 
- Django Commands to insert Fake Data?
  - `faker` `pip install Faker` + `pip install colorama`
  - Based on Products/Inventory we could use `py manage.py create_ws_data -n 10 -m Inventory` *to create 10 Testing Inventory Data* 
- Warehouse Staff User Story:
  -  Inventory Management Page 
  -  [Searching](https://learndjango.com/tutorials/django-search-tutorial) Inventory based off SKU 
     - **Parent Search HTML** where we create a *block* use *variables* then in our **Child template** we use the *block* and supply the *variables*
     - `{% with var=val var2=val2 %}`  
     - Form sends a `GET` request without a *csrf token* which redirects us BACK to our current page **WITH URL PARAMS**
     - use `Q` with `filter` to search our model based on `request.GET.get('url_param')`   
  - ~~View Specific Inventory based off SKU~~
  -  Create new inventory and product
     - This would suggest that Product:Inventory = One:Many relationship 
     - But we'll build an inventory by default   
     - Forms appear as Modal switching via Button on that modal 
       - Error handling, Toast message, Bootstrap form  
  -  ~~Update & Remove Inventory~~
-  Prepare to merge (github):
   -  Add and Commit any changes 
   -  `git fetch origin master` to fetch the latest changes 
   -  `git merge origin/master`
   -  Resolve conflict + add commit new changes 
   -  Push changes + pull request 
   -  `python manage.py makemigrations --merge`


**03/04** 
  - Profile Page 
    - Update Form with **help texts** and **fields** (Including *New Password*)
      - Handle Form Errors as well 
    - Display of current contact info 
    - Need to work on File Submission & Delete account 
      - `request.FILES` for our Form Class and `enctype="multipart/form-data"` for our Form Tag  
      - Bootstrap Modal to confirm Delete
  - Success/Error Message 
    - Figure out how to use `toast` + handle `form errors` 
    - Django `messages`
      - Custom tags in `settings.py`. Our `base.html` (which we extend on every temp) houses our toast and has a js script to show it 
      - [Guide](https://stackoverflow.com/questions/67044129/django-messages-bootstrap-toast-how-to-make-it-work)
      - [JS Toast Event](https://joshkaramuth.com/blog/django-messages-toast-htmx/)
  - Favicon
  - Product + Inventory Management 
    - Signals => total price 
    - Signals => Create Inventory once Product is created  
    - `pip install django-extensions` to access shell_plus

**02/27**
  - Authentication System 
  - Media & Static [Files](https://dev.to/emiloju/how-to-handle-media-uploads-in-django-1kpc) 
  - [Bootstrap5](https://www.w3schools.com/django/django_add_bootstrap5.php) Integration 
    - `pip install django-bootstrap-v5` 
  - [Side](https://dev.to/codeply/bootstrap-5-sidebar-examples-38pb) Nav & Base HTML 
  - MySQL Database 
    - `pip install mysqlclient` 
  - Envrionmental Variables
    - `pip install python-dotenv` 
    - Be sure to add a `.env` with: *DEBUG_LOCAL*, *MYSQL_LOCAL_CONNECTION*, *SECRET_LOCAL_KEY*
      - **MYSQL_LOCAL_CONNECTION** should follow: `"NAME USER PASSWORD HOST PORT"`
  - Tasks to Consider:
    - Profile Page & Uploading / Display Profile Image 
    - Login/Register Display Succes/Error Message
    - Replace Home Icons 
    - Start working on the Different Management Pages 


## User Authentication 
- [x] [Custom](https://dev.to/earthcomfy/getting-started-custom-user-model-5hc) LMS User
  - Role Field (default to "Worker") Updated by **ADMINS**
  - Depending on each role, they'll be granted certain access     
- [x] Register & Login Page (Error/Success Message)
- [x] Sign Out (Error/Success Message)
- [x] Updating Profile Information 


## Order Management 

## Inventory Management 

## Route Optimzation 