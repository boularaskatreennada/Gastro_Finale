from django.db import models
from restaurant.models import *

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
        ('canceled', 'Canceled')
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    number_of_people = models.PositiveIntegerField()
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    table = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Reservation by {self.client.user.username} on {self.datetime}"