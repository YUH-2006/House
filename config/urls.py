from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from properties import views as properties_views

# --- THÊM 2 DÒNG IMPORT NÀY VÀO ĐỂ HẾT LỖI SYNTAX ---
from django.conf import settings
from django.conf.urls.static import static
# ---------------------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('properties.urls')),
    
    # Đường dẫn login chạy qua hàm phân luồng custom
    path('login/', properties_views.custom_login, name='login'),
    
    # THÊM DÒNG NÀY VÀO ĐỂ LÀM ĐƯỜNG DẪN LOGOUT:
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
] 

# Cấu hình hiển thị file ảnh media trong môi trường phát triển (DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)