from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import authenticate, login # Nhớ import thêm 2 hàm này để xử lý đăng nhập
from .models import Property

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

# 4. Hàm đăng nhập phân luồng (MỚI THÊM VÀO ĐÂY)
def custom_login(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        
        # Xác thực tài khoản mật khẩu
        user = authenticate(request, username=u_name, password=p_word)
        
        if user is not None:
            login(request, user) # Đăng nhập vào hệ thống
            
            # Nếu là Admin/Staff -> Vào thẳng trang quản trị
            if user.is_staff: 
                return redirect('/admin/') 
            # Nếu là User thường -> Về trang chủ phối cảnh nhà đất
            else:
                return redirect('home')    
        else:
            return render(request, 'properties/login.html', {'error': 'Sai tài khoản hoặc mật khẩu!'})
            
    return render(request, 'properties/login.html')