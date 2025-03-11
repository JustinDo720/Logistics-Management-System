from django.db import models
from django.utils.text import slugify
from random import randint 
from django.core.validators import MinValueValidator
from decimal import Decimal
from workers.models import LMSWorker
from django.core.mail import send_mail
from django.conf import settings
from geopy.geocoders import Nominatim
import openrouteservice as ors 
import time 
import os
from django.utils import timezone
from datetime import datetime

# Create your models here.

class Order(models.Model):
    status_choices = [
        ('Received', 'Received'),
        ('In-Transit', 'In Transit'),
        ('Delivered', 'Delivered')
    ]

    priority_level_choices = [
        ('Medium', 'Medium'),
        ('High', 'High')
    ]

    # This is a Long/Lat of Tekbasic's Location
    HEADQUARTERS_COORDS = [-74.52976762042528, 40.41706977125244]

    customer_name = models.CharField(max_length=150)
    order_slug = models.SlugField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=status_choices, default='Received')
    priority_level = models.CharField(max_length=30, choices=priority_level_choices, default='Medium')
    destination_address = models.CharField(max_length=300)


    # https://stackoverflow.com/questions/12384460/allow-only-positive-decimal-numbers
    total_price = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.01'))])

    @staticmethod
    def gen_id():
        return randint(10000, 999999)

    # Generating slug 
    def gen_slug(self):
        # First&Last Letter of CustomerName-order_id-counter 
        generated_id = Order.gen_id() 
        c_name_letters = f'{self.customer_name[0].upper()}{self.customer_name[-1].upper()}'
        slug = f'{c_name_letters}-{generated_id}'
        my_slug = slug 

        counter = 1
        while Order.objects.filter(order_slug=my_slug).exists():
            my_slug = f'{slug}-{counter}'
            counter += 1
        return my_slug        
    
    # Once saved, we'll generated our order_slug 
    def save(self, *args, **kwargs):
        if not self.order_slug:
            self.order_slug = self.gen_slug() 

        # Since we moved our logic to a seperate model, we'll be doing on signals
        # # Generating our route 
        # if not self.route_coords and not self.route_eta and not self.route_miles:
        #     self.build_route()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name

# Routing 
class Route(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    # Routing (If these class variables don't exist THEN we'll run our route functions)
    # https://docs.djangoproject.com/en/5.0/topics/db/queries/#querying-jsonfield
    route_coords = models.JSONField(null=True, blank=True)
    # We use FloatField because DecimalField would require a max_digit 
    route_eta = models.FloatField(null=True, blank=True)
    route_miles = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    # Building our Routing 
    # Helper functions to convert 
    def get_miles(self):
        return round(self.route_miles/1609, 2)

    def get_eta(self):
        return time.strftime('%H:%M:%S', time.gmtime(self.route_eta))

    def find_coords(self):
        # Tekbasic Address (Long Lat) Because of Route
        head_quarters_coords = Order.HEADQUARTERS_COORDS

        # Building our geolocter 
        if self.order.destination_address:
            geolocator = Nominatim(user_agent="lms_app")
            loc = geolocator.geocode(self.order.destination_address)
            if loc:
                time.sleep(1)   # Avoid constant request to OpenStreetMap API 
                # Returning Long Lat because we're using this coord to build our route with ors
                return [head_quarters_coords,[loc.longitude, loc.latitude]]
        return None     # Invalid Address or Empty Address
    
    def build_route(self, route_profile='driving-car'):
        coords = self.find_coords()
        if coords:
            client = ors.Client(key=os.getenv('ORS_API_KEY'))
            route = client.directions(
                coordinates=coords,
                profile=route_profile,
                format='geojson'    # Must use geojson format to return our numbered coordinates instead of google coords objects
            )
            # Since this is a json field we could put in an array
            self.route_coords = route['features'][0]['geometry']['coordinates']
            # We use FloatField because DecimalField would require a max_digit 
            self.route_eta = route['features'][0]['properties']['summary']['duration']   # Seconds 
            self.route_miles = route['features'][0]['properties']['summary']['distance'] # Meters 
            # Event though we set the properties in here we MUST save it to our database (Had an issue where route data wasn't saving)
            # self.save()   ## We'll save after we build route 
            return True 
        return None     # No route because coords doesn't exist 
    

    # Any update to this Route we want to make sure we record the date time 
    def save(self, *args, **kwargs):
        # datetime.now() to get the current local time instead of timezone.now() 
        self.last_updated = datetime.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.order.order_slug} Route'

class OrderStatusHistory(models.Model):
    status_choices = [
        ('Received', 'Received'),
        ('In-Transit', 'In Transit'),
        ('Delivered', 'Delivered')
    ]

    class Meta:
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=50, choices=status_choices, default='Receive')
    status_msg = models.CharField(max_length=450, null=True, blank=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    # We'll update the last_updated DateTimeField to use datetime now instead of timezone now
    def save(self, *args, **kwargs):
        self.last_updated = datetime.now() 
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.order.order_slug} {self.status}'


class Product(models.Model):
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    # sku is our Unique Identifier 
    sku = models.SlugField(blank=True, null=True, unique=True)   # Auto Generated 
    date = models.DateField(auto_now_add=True)


    # Methods
    @staticmethod
    def gen_id():
        return randint(10000, 99999)

    def gen_sku(self):
        # Stock Keeping Unit -->  Category-ProductName-Identifier
        category_slug = slugify(self.category)
        product_slug = slugify(self.product_name)
        product_id = Product.gen_id()
        slug = f'{category_slug}-{product_slug}-{product_id}'
        my_slug = slug 

        # Making sure our slug is unique 
        counter = 1
        while Product.objects.filter(sku=my_slug).exists():
            # We'll add our counter  
            my_slug = f'{slug}-{counter}'
            # If that slug still exists we'll keep incrementing 
            counter += 1
        return my_slug
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.gen_sku()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sku

class Inventory(models.Model):
    # Instead of one-to-one perhaps we could do one prduct to many inventories 
    # Still use signals to create a Default Inventory, users could add more 
    # Think of it as One product could have multiple inventories from different warehouses   
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')  
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_threshold = models.IntegerField(default=50, validators=[MinValueValidator(0)])
    restock = models.BooleanField(default=True)
    notified = models.BooleanField(default=False)   # Preventing Email Spam 
    # Since we're using signals to create, we'lll set the location field as optional
    location = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories' 

    # Sending Email 
    def send_notification(self):
        # Assuming we handled the Restock logic in signals.py 
        if not self.notified: 
            # Send Notification 
            self.notified = True 
            # Grabbing all our users that want to be notified with this Inventory 
            users_to_notify = self.notifications.all()
            # We access all the potential notification object from that queryset: access the user to access their emails
            emails = [notify_obj.user.email for notify_obj in users_to_notify]
            if emails:
                res = send_mail(
                        "Low Stock Alert",
                        f"The stock for {self.product.product_name} is low at the inventory location:  {self.location} ID:{self.id}!",
                        settings.EMAIL_HOST_USER,
                        emails,
                        fail_silently=True, # doesn't crash our program
                    )
                return res

    # Checking stock
    def check_inv(self):
        # Trigger Restock notification (Maybe email works but for now...)
        self.restock = True if self.stock <= self.stock_threshold else False 
        return self.restock


    def __str__(self):
        return f'{self.product.product_name}: {self.stock} left' if not self.restock else f'{self.product.product_name}: NEEDS RESTOCK! {self.stock}/{self.stock_threshold}'

class OrderItem(models.Model):
    # order_item_slug is our Unique Identifier 
    order_item_slug = models.SlugField(null=True, blank=True, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    date = models.DateField(auto_now_add=True)
    
    inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')  # Track inventory location

    # Generating an order_id
    @staticmethod
    def gen_id():
        return randint(1,999999)
    
    def gen_order_id(self):
        # We'll have the customer_name + a generated id + counter 
        c_name_slug = slugify(self.order.customer_name)
        generated_id = OrderItem.gen_id()
        slug = f'{c_name_slug}-{generated_id}' 
        my_order_id = slug

        counter = 1 
        while OrderItem.objects.filter(order_item_slug=my_order_id).exists():
            my_order_id = f'{slug}-{counter}'
            counter += 1
        
        return my_order_id

    def save(self, *args, **kwargs):
        # If an order_item_slug doesnt exist on .save() function, we'll generate one
        if not self.order_item_slug:
            self.order_item_slug = self.gen_order_id()

        # Forward all arguments + keyword arguemnts to carry out the original .save() function 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.customer_name}: {self.order_item_slug}"
    

class InventoryNotification(models.Model):
    # Inventory will have access Users who want to stay updated with that inventory 
    # If that inventory turns low it sends an email to ALL users that want to stay notified 
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='notifications')
    # Of course we need to find the user who wants to be associated with this notification to access email 
    user = models.ForeignKey(LMSWorker, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    notification_slug = models.SlugField(blank=True, null=True, unique=True)

    # With notification slug we could find if the user accidentally notified twice 
    def gen_slug(self):
        slug = f'{self.user.username}-{self.inventory.location}-{slugify(self.inventory.product.product_name)}'
        
        # We don't need to check for unqiueness because we want there to be exactly one record of the users notification 
        return slug 
    
    def save(self, *args, **kwargs):
        if not self.notification_slug:
            self.notification_slug = self.gen_slug() 
        super().save(*args, **kwargs)

    def __str__(self):
        return self.notification_slug