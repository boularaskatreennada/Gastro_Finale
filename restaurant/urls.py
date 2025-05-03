from django.urls import path
from . import views

urlpatterns = [
    path('pdg-dashboard/', views.pdg_dashboard, name='pdg_dashboard'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.client_register, name='client_register'),
    
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('Gastrolink/', views.landing_page , name='landing_page'),

    path('restaurants/', views.restaurant_list, name='restaurants'),
    path('restaurants/add/', views.add_restaurant, name='add_restaurant'),
    path('restaurants/edit/<int:pk>/', views.edit_restaurant, name='edit_restaurant'),
    path('restaurants/delete/<int:pk>/', views.delete_restaurant, name='delete_restaurant'),
    path('restaurants/<int:restaurant_id>/information/', views.restaurant_information, name='restaurant_information'),
    
    path('employees/', views.employee_list, name='employee_list'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('employees/edit/<int:pk>/', views.edit_employee, name='edit_employee'),
    path('managers/delete/<int:pk>/', views.delete_manager, name='delete_manager'),
    path('suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),

    path('employees_Manager/', views.employee_manager_list, name='employee_manager_list'),
    path('staff/add/', views.add_staff_employee, name='add_staff'),
    path('staff/<str:role>/<int:pk>/edit/', views.edit_staff_employee, name='edit_staff'),
    path('staff/<str:role>/<int:pk>/delete/', views.delete_staff_employee, name='delete_staff'),
]  