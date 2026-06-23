from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('house/<int:pk>/', views.property_detail, name='property_detail'),
    path('register/', views.register, name='register'),
    path('predict/', views.predict_price, name='predict'),
]