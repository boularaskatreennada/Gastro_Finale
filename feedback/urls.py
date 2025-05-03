from django.urls import path
from . import views

urlpatterns = [
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/add/', views.add_feedback_or_complaint, name='add_review'),
]
