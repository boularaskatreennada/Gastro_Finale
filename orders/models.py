from django.db import models
from restaurant.models import *
from menu.models import Dish
from offers.models import *

class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PREPARING = 'preparing', 'Preparing'
    DONE = 'done', 'Done'
    CANCELED ='canceled', 'Canceled'
    PAID = 'paid' ,'Paid'

class OrderMode(models.TextChoices):
    SERVED = 'served', 'Served'
    DELIVERED = 'delivered', 'Delivered'
    TAKEAWAY = 'take-away', 'Take-away'

class Order(models.Model):
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=OrderStatus.choices)
    mode = models.CharField(max_length=10, choices=OrderMode.choices)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    server = models.ForeignKey(Server, on_delete=models.SET_NULL, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    table_number = models.PositiveIntegerField(null=True, blank=True)
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    @property
    def total_before_discount(self):
        return self.total_amount + self.discount_amount
    
    @property 
    def discount_applied(self):
        return self.discount_amount > 0

    def __str__(self):
        return f"Order #{self.id} at {self.restaurant.name} - Table {self.table_number if self.table_number else 'N/A'}"
    @property
    def total_amount(self):
       order_dishes = self.orderdish_set.select_related('dish')
       return sum(od.quantity * od.dish.price for od in order_dishes)

class OrderDish(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('order', 'dish')

class DeliveryStatus(models.TextChoices):
    PENDING ='pending', 'Pending'
    DELIVERED = 'delivered', 'Delivered'
    INPROGRESS = 'in-progress', 'In-progress'
    
class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    delivery_person = models.ForeignKey(DeliveryPerson, on_delete=models.CASCADE,null=True, blank=True)
    delivery_date = models.DateTimeField()
    status = models.CharField(max_length=50,choices=DeliveryStatus.choices)
    address= models.CharField(max_length=255, blank=True, null=True)
    notified = models.BooleanField(default=False)