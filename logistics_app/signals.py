# https://www.geeksforgeeks.org/how-to-create-and-use-signals-in-django/
from django.db.models.signals import post_save, pre_save
from .models import Product, Inventory, OrderItem, Order
from django.dispatch import receiver


# Create an Inventory immediately after a Product has been made 
@receiver(post_save, sender=Product)
def create_inventory(sender, instance, created, **kwargs):
    # If our instance was created then we'll create an Inventory for that product 
    if created:
        inv = Inventory.objects.create(product=instance, location='DEFAULT')
        # Once our Inventory is created we actually need to save this Inventory 
        inv.save()  # Save here is fine because Inventory isnt out sender 


# Calculating total price after an order item is saved/updated
@receiver(post_save, sender=OrderItem)
def update_order_total_price(sender, instance, **kwargs):
    # When a OrderItem is altered we ALWAYS want to make sure their changes reflect the total_price 
    our_order = instance.order
    new_total = 0 
    # We reference back to our order then grab ALL order_items associated with our order
    for ot in our_order.order_items.all():
        new_total += (ot.product.price * ot.quantity)

    # If our new price is different from total_price:
    if float(new_total) != our_order.total_price: 
        our_order.total_price = float(new_total)
        our_order.save()
    else:
        pass 

# Before saving our inventory we always want to check our stock vs threshold
@receiver(pre_save, sender=Inventory)
def check_inv_stock(sender, instance, **kwargs):
    # Whenever we alter Inventory we ALWAYS have to check our stock and set restock accordingly 
    instance.check_inv()