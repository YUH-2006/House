from django.shortcuts import render
from .models import Property

def home(request):
    # Lấy toàn bộ danh sách nhà đất từ Database ra
    tat_ca_nha = Property.objects.all().order_by('-ngay_dang')
    return render(request, 'properties/home.html', {'properties': tat_ca_nha})