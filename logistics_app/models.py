from django.db import models
from django.utils.text import slugify
from random import randint 
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.

class Order(models.Model):
    status_choices = [
        ('receive', 'Received'),
        ('in-transit', 'In Transit'),
        ('delivered', 'Delivered')
    ]

    priority_level_choices = [
        ('medium', 'Medium'),
        ('high', 'High')
    ]

    customer_name = models.CharField(max_length=150)
    order_slug = models.SlugField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=status_choices, default='receive')
    priority_level = models.CharField(max_length=30, choices=priority_level_choices, default='medium')
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

        # Maybe we should do signals with the total_price 
        # if not self.total_price:
        #     # Query every order_item and sum them 
        #     amount = 0 
        #     for item in self.order_items.all():
        #         price = item.product.price * item.quantity
        #         amount += price  
        #     self.total_price = amount 

        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name


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


class OrderItem(models.Model):
    # order_item_slug is our Unique Identifier 
    order_item_slug = models.SlugField(null=True, blank=True, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    date = models.DateField(auto_now_add=True)

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
    

class Inventory(models.Model):
    # Instead of one-to-one perhaps we could do one prduct to many inventories 
    # Still use signals to create a Default Inventory, users could add more 
    # Think of it as One product could have multiple inventories from different warehouses   
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')  
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_threshold = models.IntegerField(default=50, validators=[MinValueValidator(0)])
    restock = models.BooleanField(default=True)
    # Since we're using signals to create, we'lll set the location field as optional
    location = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories' 

    # Checking stock
    def check_inv(self):
        # Trigger Restock notification (Maybe email works but for now...)
        self.restock = True if self.stock <= self.stock_threshold else False 

    def __str__(self):
        return f'{self.product.product_name}: {self.stock} left' if not self.restock else f'{self.product.product_name}: NEEDS RESTOCK! {self.stock}/{self.stock_threshold}'
