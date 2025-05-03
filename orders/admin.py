from django.contrib import admin
from .models import Order, OrderDish, Delivery

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_date', 'status', 'mode', 'client', 'server', 'restaurant')
    list_filter = ('status', 'mode')
    search_fields = ('client__email',)

admin.site.register(OrderDish)
admin.site.register(Delivery)