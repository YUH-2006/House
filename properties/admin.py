from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('tieu_de', 'loai_nha', 'gia', 'dien_tich', 'ngay_dang')
    list_filter = ('loai_nha', 'ngay_dang')
    search_fields = ('tieu_de', 'dia_chi')