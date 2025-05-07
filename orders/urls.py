from django.urls import path
from . import views

urlpatterns = [
   path('manager/orders/', views.orderslistManager, name='clients_orders_list'),
   path('manager/complaints/<int:complaint_id>/update/', views.update_complaint_status, name='update_complaint_status'),
   path('order/', views.clientOrder, name='order'),
   path('place_order/', views.placeOrderClient, name='placeOrderClient'),
   path('confirm_order/<int:order_id>/', views.confirm_order, name='confirm_order'),  
   
   path('ordersList/', views.orders_list, name='ordersList'),
   path('update-status/<int:pk>/', views.update_order_status, name='update_order_status'),
   path('cancel_order/<int:pk>/', views.cancel_order, name='cancel_order'),
   path('edit_order/<int:pk>/', views.edit_order, name='edit_order'),
   path('takeOrder/', views.take_order, name='takeOrder'),
   path('placeOrder/', views.placeOrder, name='place_order'),
   path('ordersListChef/', views.order_list_chef, name='ordersListChef'),
   path('deliveryOrders/',views.delivery_orders,name='DeliveryOrders'),
   path('NotificationDel/',views.delivery_orders,name='NotificationsDel'),
]

