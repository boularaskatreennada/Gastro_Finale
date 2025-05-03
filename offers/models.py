from django.db import models
from django.utils import timezone

class OfferStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    UPCOMING = 'upcoming', 'Upcoming'
    EXPIRED = 'expired', 'Expired'

class Offer(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    discount = models.FloatField()
    code = models.CharField(max_length=50, unique=True)
    uses = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='offers_images/', blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    @property
    def status(self):
        today = timezone.now().date()
        if today < self.start_date:
            return OfferStatus.UPCOMING
        elif self.start_date <= today <= self.end_date:
            return OfferStatus.ACTIVE
        else:
            return OfferStatus.EXPIRED
    
    def save(self, *args, **kwargs):
        # Ensure end date is after start date
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date")
        super().save(*args, **kwargs)