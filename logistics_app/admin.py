from django.contrib import admin

# Register your models here.
from . import models

models_to_register = [
    models.Order,
    models.OrderItem,
    models.Product,
    models.Inventory,
    models.InventoryNotification,
    models.Route,
    models.OrderStatusHistory
]

for model in models_to_register:
    admin.site.register(model)

