
from django.urls import path
from . import views

urlpatterns = [
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_create'),
    path('update/<int:pk>/', views.expense_update, name='expense_update'),
    path('delete/<int:pk>/', views.expense_delete, name='expense_delete'),
]
