from django.db import models
from restaurant.models import *


class Review(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    date = models.DateField(auto_now_add=True)

class ComplaintStatus(models.TextChoices):
    RESPONDED = 'responded', 'Responded'
    UNRESPONDED = 'not_responded', 'Not Responded'

class Complaint(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateField()
    status = models.CharField(max_length=15, choices=ComplaintStatus.choices)
