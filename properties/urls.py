from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('house/<int:pk>/', views.property_detail, name='property_detail'),
    path('register/', views.register, name='register'),
    path('predict/', views.predict_price, name='predict'),
    # THÊM DÒNG NÀY ĐỂ MỞ CỔNG CHO TAB CHAT
    path('chat/', views.chat_tu_van, name='chat_tu_van'),
]