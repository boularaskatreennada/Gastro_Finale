# expenses/views.py
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Expense
from .forms import ExpenseForm
from restaurant.models import *
from restaurant.decorators import manager_required
from restaurant.decorators import pdg_required

@manager_required
def expense_list(request):
    try:
        restaurant = request.user.manager.restaurant
    except (AttributeError, Manager.DoesNotExist):
        return HttpResponseForbidden("You are not allowed to view this page.")

    expenses = Expense.objects.filter(restaurant=restaurant).order_by('-expense_date')
    return render(request, 'manager/expenses.html', {'expenses': expenses})

@manager_required
def expense_create(request):
    try:
        restaurant = request.user.manager.restaurant
    except (AttributeError, Manager.DoesNotExist):
        return HttpResponseForbidden("You are not allowed to create expenses.")

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.restaurant = restaurant
            expense.created_by = request.user
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()

    return render(request, 'manager/addExpense.html', {'form': form})


@manager_required
def expense_update(request, pk):
    try:
        restaurant = request.user.manager.restaurant
    except (AttributeError, Manager.DoesNotExist):
        return HttpResponseForbidden("You are not allowed to edit this expense.")

    expense = get_object_or_404(Expense, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'manager/addExpense.html', {'form': form})

@manager_required
def expense_delete(request, pk):
    try:
        restaurant = request.user.manager.restaurant
    except (AttributeError, Manager.DoesNotExist):
        return HttpResponseForbidden("You are not allowed to delete this expense.")

    expense = get_object_or_404(Expense, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        expense.delete()
        return redirect('expense_list')

    return render(request, 'manager/expenses.html', {'expense': expense})