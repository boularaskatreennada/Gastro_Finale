from django.urls import path
from . import views

urlpatterns = [

    path('menu/', views.menu_view, name='menu'),
    path('menu/add/', views.add_plate, name='add_plate'),
    path('menu/edit/<int:pk>/', views.edit_plate, name='edit_plate'),
    path('menu/delete/<int:pk>/', views.delete_plate, name='delete_plate'),

    path('ingredients/', views.ingredients_view, name='ingredients'),
    path('ingredients/<int:pk>/', views.ingredients_view, name='ingredients'),
    path('ingredients/delete/<int:pk>/', views.delete_ingredient, name='delete_ingredient'),


    path('menu-manager/', views.manager_daily_menu, name='manager_daily_menu'),
    path('get-dishes/', views.get_dishes_by_category, name='get_dishes_by_category'),
    path('get-daily-menu/', views.get_daily_menu, name='get_daily_menu'),
    path('add-dish/', views.add_dish_to_daily_menu, name='add_dish_to_daily_menu'),
    path('remove-dish/<int:daily_menu_dish_id>/', views.remove_dish_from_daily_menu, name='remove_dish_from_daily_menu'),

    path('manager/orders/', views.generate_shopping_list, name='generate_shopping_list'),
]
