from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import authenticate, login
from .models import Property

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

# 5. Hàm dự đoán giá nhà bằng AI (ĐẢM BẢO CÓ HÀM NÀY Ở ĐÂY)
def predict_price(request):
    ket_qua = None
    if request.method == 'POST':
        dien_tich = float(request.POST.get('dien_tich', 0))
        so_phong = int(request.POST.get('so_phong', 0))
        
        # Đường dẫn tới file bot_du_doan.pkl ở thư mục gốc dự án
        bot_path = os.path.join(settings.BASE_DIR, 'bot_du_doan.pkl')
        
        if os.path.exists(bot_path):
            bot = joblib.load(bot_path)
            du_doan = bot.predict([[dien_tich, so_phong]])
            ket_qua = round(du_doan[0], 2)
        else:
            ket_qua = "Chưa tìm thấy file bot_du_doan.pkl! Bạn nhớ chạy file train_bot.py trước nhé."

    return render(request, 'properties/predict.html', {'ket_qua': ket_qua})