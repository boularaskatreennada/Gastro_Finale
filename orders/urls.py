from django.urls import path
from . import views

urlpatterns = [
   path('manager/orders/', views.orders_list, name='clients_orders_list'),
   path('manager/complaints/<int:complaint_id>/update/', views.update_complaint_status, name='update_complaint_status'),

   path('order/', views.clientOrder, name='order'),
   path('place_order/', views.place_order, name='place_order'),
   path('confirm_order/<int:order_id>/', views.confirm_order, name='confirm_order'),

]

