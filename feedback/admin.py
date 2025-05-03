from django.contrib import admin
from .models import Review, Complaint

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'rating', 'comment', 'date')
    list_filter = ('rating', 'date')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('client', 'restaurant', 'message', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('client__email',)