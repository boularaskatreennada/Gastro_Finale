from django.urls import path
from . import views

urlpatterns = [
     path('create/', views.create_reservation, name='create_reservation'),
      path('reservedTables/', views.reserved_tables, name='reserved_tables'),
    path('update_reservation/<int:pk>/', views.update_reservation, name='update_reservation'),
    path('cancel_reservation/<int:pk>/', views.cancel_reservation, name='cancel_reservation'),
    path('update_reservation_status/<int:pk>/', views.update_reservation_status, name='update_reservation_status'),
    
]  