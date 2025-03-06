from django.db import models

# Create your models here.

class Order(models.Model):
    status_choices = [
        ('Receive', 'Received'),
        ('In-Transit', 'In Transit'),
        ('Delivered', 'Delivered')
    ]

    priority_level_choices = [
        ('Medium', 'Medium'),
        ('High', 'High')
    ]

    customer_name = models.CharField(max_length=150)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=status_choices, default='Receive')
    priority_level = models.CharField(max_length=30, choices=priority_level_choices, default='Medium')
    destination_address = models.CharField(max_length=300)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.customer_name
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.order.customer_name}-{self.quantity}"