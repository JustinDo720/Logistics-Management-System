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
    """
        We need to build a logic to send an email but refrain from email spamming 
        
        Problem with initial logic:
            - Each time we save the restock field might still be false so we CAN'T send an email based on restock being JUST false 

        My Solution (for now):
            - We check if there's a change between restock being False to True (thats when we want to send an email)

        Why are we putting that logic here?
            - Well this is pre-save meaning we could actually check the values BEFORE + AFTER the save so if the two values diff then we could execute our email based on condition
            - If the condition is true we'll set the flag 'notified' flag to False and run our send_notificaiton method which ONLY sends an email if notified is False 
            - else we make sure that flag is True
        
        Notified is True IF an email has already been sent OR its on stand-by waiting for a change in Restock 
    """

    # Pre-save means we have not saved the data yet therefore we still have access to the original instance 
    original_inv = Inventory.objects.filter(id=instance.id).first() 
    # The edge case we're catching is the fact that Inventory was newly created so this makese sure there was an original inventory 
    original_restock = original_inv.restock if original_inv else None 
    # Whenever we alter Inventory we ALWAYS have to check our stock and set restock accordingly 
    saved_restock = instance.check_inv()

    # Remember we're targeting a change between False --> True 
    # We use is comparison instead of ""=="" or "!=" 
    if original_restock is False and saved_restock is True:
        print('Change in Restock')
        # This means there was a change in our restock field 
        # Let' send our email then set the notified flag  
        instance.notified = False 
        notification_status = instance.send_notification()
        if notification_status:
            # Email sent successfully
            instance.notified = True 
        else:
            print('Issue sending that email')
    else:
        print('Not notifying')
        instance.notified = True 