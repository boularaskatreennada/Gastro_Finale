from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'amount', 'description', 'expense_date')
    list_filter = ('restaurant',)