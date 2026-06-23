from django.db import models
from django.contrib.auth.models import User

class Property(models.Model):
    LOAI_NHA_CHOICES = [
        ('CH', 'Chung cư'),
        ('NP', 'Nhà phố'),
        ('ĐN', 'Đất nền'),
    ]

    tieu_de = models.CharField(max_length=200, verbose_name="Tiêu đề")
    loai_nha = models.CharField(max_length=2, choices=LOAI_NHA_CHOICES, default='NP', verbose_name="Loại nhà")
    dia_chi = models.CharField(max_length=255, verbose_name="Địa chỉ")
    gia = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Giá (VND)")
    dien_tich = models.FloatField(verbose_name="Diện tích (m²)")
    mo_ta = models.TextField(verbose_name="Mô tả chi tiết")
    hinh_anh = models.ImageField(upload_to='properties/', verbose_name="Hình ảnh")
    ngay_dang = models.DateTimeField(auto_now_add=True)
    nguoi_dang = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người đăng")

    def __str__(self):
        return self.tieu_de