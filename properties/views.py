from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import authenticate, login
from .models import Property
import pandas as pd  # <--- THÊM CHÍNH XÁC DÒNG NÀY VÀO ĐẦU FILE VIEWS.PY

# --- THÊM THƯ VIỆN ĐỂ CHẠY BOT DỰ ĐOÁN GIÁ AI ---
import joblib
import os
from django.conf import settings
# -----------------------------------------------

# 1. Hàm xem trang chủ (Bắt buộc đăng nhập)
@login_required
def home(request):
    tat_ca_nha = Property.objects.all().order_by('-ngay_dang')
    return render(request, 'properties/home.html', {'properties': tat_ca_nha})

# 2. Hàm xem chi tiết nhà
def property_detail(request, pk):
    house = get_object_or_404(Property, pk=pk)
    return render(request, 'properties/detail.html', {'house': house})

# 3. Hàm đăng ký thành viên
def register(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        re_p_word = request.POST.get('re_password')
        
        if User.objects.filter(username=u_name).exists():
            return render(request, 'properties/register.html', {'error': 'Tài khoản này đã tồn tại!'})
            
        if p_word != re_p_word:
            return render(request, 'properties/register.html', {'error': 'Mật khẩu xác nhận không trùng khớp!'})
            
        User.objects.create_user(username=u_name, password=p_word)
        return redirect('login')
        
    return render(request, 'properties/register.html')

# 4. Hàm đăng nhập phân luồng 
def custom_login(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        
        user = authenticate(request, username=u_name, password=p_word)
        
        if user is not None:
            login(request, user)
            if user.is_staff: 
                return redirect('/admin/') 
            else:
                return redirect('home')    
        else:
            return render(request, 'properties/login.html', {'error': 'Sai tài khoản hoặc mật khẩu!'})
            
    return render(request, 'properties/login.html')

def predict_price(request):
    if request.method == 'POST':
        # 1. Thu thập trọn bộ dữ liệu từ form chatbot gửi lên
        dien_tich = float(request.POST.get('dien_tich', 0))
        so_phong_ngu = int(request.POST.get('so_phong_ngu', 1))
        so_phong_tam = int(request.POST.get('so_phong_tam', 1))
        khu_vuc = request.POST.get('khu_vuc', 'Quận 1')
        loai_nha = request.POST.get('loai_nha', 'Nhà phố')
        vi_tri = request.POST.get('vi_tri', 'Mặt tiền')
        nam_xay_dung = int(request.POST.get('nam_xay_dung', 2024))

        # 2. Tạo DataFrame đúng cấu trúc mảng mà bộ não AI đã học
        input_data = pd.DataFrame([{
            'dien_tich': dien_tich,
            'so_phong_ngu': so_phong_ngu,
            'so_phong_tam': so_phong_tam,
            'khu_vực': khu_vuc,
            'loai_nha': loai_nha,
            'vi_tri': vi_tri,
            'nam_xay_dung': nam_xay_dung
        }])

        # 3. Tải bộ não AI lên tính toán định giá nhà
        model = joblib.load('bot_du_doan_nang_cap.pkl')
        gia_du_doan = model.predict(input_data)[0] # Kết quả gốc (Triệu VND)

        # 4. Tính toán các chỉ số bổ sung mở rộng theo nghiệp vụ BĐS
        gia_thap_nhat = round(gia_du_doan * 0.9, 1) # Khoảng thấp nhất -10%
        gia_cao_nhat = round(gia_du_doan * 1.1, 1) # Khoảng cao nhất +10%
        gia_tren_m2 = round(gia_du_doan / dien_tich, 2) if dien_tich > 0 else 0
        
        # Phân loại phân khúc bất động sản
        if gia_du_doan < 2000:
            phan_loai = "Phân khúc Nhà Giá Rẻ"
        elif 2000 <= gia_du_doan <= 7000:
            phan_loai = "Phân khúc Nhà Trung Cấp"
        else:
            phan_loai = "Phân khúc BĐS Cao Cấp"

        # 5. Đóng gói gửi toàn bộ thông tin chi tiết ra trang hiển thị
        context = {
            'gia_uoc_tinh': round(gia_du_doan, 1),
            'gia_thap_nhat': gia_thap_nhat,
            'gia_cao_nhat': gia_cao_nhat,
            'gia_tren_m2': gia_tren_m2,
            'phan_loai': phan_loai,
            'dien_tich': dien_tich,
            'khu_vuc': khu_vuc
        }
        return render(request, 'properties/predict.html', context)
        
    return render(request, 'properties/predict.html')