from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import authenticate, login
from .models import Property
import pandas as pd
import joblib
import os
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)

GEMINI_MODEL_NAMES = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
]

MODEL_PATH = 'bot_du_doan_nang_cap.pkl'
DATASET_MODEL = None
if os.path.exists(MODEL_PATH):
    try:
        DATASET_MODEL = joblib.load(MODEL_PATH)
    except Exception as exc:
        print(f"Không tải được model dataset: {exc}")


def get_gemini_reply(prompt):
    if not GEMINI_API_KEY:
        raise RuntimeError("Chưa cấu hình API key Gemini")

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 300,
        },
    }

    last_error = None
    for model_name in GEMINI_MODEL_NAMES:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, timeout=60)
        except requests.exceptions.RequestException as exc:
            last_error = RuntimeError(f"Lỗi kết nối Gemini với {model_name}: {exc}")
            continue

        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                last_error = RuntimeError(f"Gemini {model_name} không trả về câu trả lời")
                continue

            parts = candidates[0].get("content", {}).get("parts", [])
            reply = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
            return reply.strip() or ""

        if response.status_code == 403:
            last_error = RuntimeError(
                "Gemini chưa được cấp quyền truy cập. Vui lòng kiểm tra billing hoặc quyền API trên Google Cloud."
            )
            continue

        if response.status_code == 429:
            raise RuntimeError(
                "Gemini bị giới hạn quota. Vui lòng kiểm tra billing hoặc chờ một lúc rồi thử lại."
            )

        last_error = RuntimeError(
            f"Gemini {model_name} trả về lỗi {response.status_code}: {response.text[:300]}"
        )

    if last_error:
        raise last_error
    raise RuntimeError("Gemini API không trả về kết quả")


def get_dataset_reply(user_message):
    if DATASET_MODEL is None:
        return None

    text = user_message.lower()
    dien_tich = None
    so_phong_ngu = 2
    khu_vuc = 'Hà Nội'
    loai_nha = 'Nhà phố'
    vi_tri = 'Mặt tiền'
    nam_xay_dung = 2026

    # Giải thích: cố gắng trích xuất vài thông số từ câu hỏi
    import re
    dt_match = re.search(r'(\d+[\.,]?\d*)\s*(m2|m²|mét vuông)', text)
    if dt_match:
        dien_tich = float(dt_match.group(1).replace(',', '.'))

    pn_match = re.search(r'(\d+)\s*(phòng ngủ|pn|phòng)', text)
    if pn_match:
        so_phong_ngu = min(int(pn_match.group(1)), 8)

    if 'hcm' in text or 'hồ chí minh' in text or 'sài gòn' in text:
        khu_vuc = 'Hồ Chí Minh'
    elif 'hà nội' in text or 'hn' in text:
        khu_vuc = 'Hà Nội'
    elif 'đà nẵng' in text:
        khu_vuc = 'Đà Nẵng'

    if 'chung cư' in text or 'căn hộ' in text:
        loai_nha = 'Chung cư/Phòng trọ'
    elif 'nhà phố' in text or 'nhà' in text:
        loai_nha = 'Nhà phố'

    if 'mặt tiền' in text:
        vi_tri = 'Mặt tiền'
    elif 'ngõ' in text or 'hẻm' in text:
        vi_tri = 'Trong ngõ'

    if dien_tich is None:
        return None

    df = pd.DataFrame([{
        'dien_tich': dien_tich,
        'so_phong_ngu': so_phong_ngu,
        'so_phong_tam': 1,
        'khu_vực': khu_vuc,
        'loai_nha': loai_nha,
        'vi_tri': vi_tri,
        'nam_xay_dung': nam_xay_dung,
    }])

    try:
        predicted_price = DATASET_MODEL.predict(df)[0]
        return f"Dựa trên dữ liệu thị trường hiện có, giá ước tính khoảng {round(predicted_price,1):,} triệu VND."
    except Exception:
        return None


def build_fallback_reply(user_message):
    dataset_response = get_dataset_reply(user_message)
    if dataset_response:
        return dataset_response

    text = user_message.lower()

    if any(keyword in text for keyword in ["giá", "mua", "bán", "thuê", "đầu tư"]):
        return (
            "Mình đang dùng chế độ phản hồi dự phòng. "
            "Để đánh giá giá nhà, bạn nên cung cấp diện tích, vị trí, số phòng ngủ, số phòng tắm và tình trạng nhà."
        )
    if any(keyword in text for keyword in ["phong thủy", "hướng", "mùi", "vượng"]):
        return "Với phong thủy, nên ưu tiên ánh sáng, thông thoáng, thoát khí và bố trí phòng ngủ hợp lý."
    return "Mình có thể hỗ trợ về giá nhà, thuê/mua, vị trí, phong thủy và các yếu tố ảnh hưởng đến giá bất động sản."


@csrf_exempt
def chat_tu_van(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'reply': 'Vui lòng nhập câu hỏi.'})

        try:
            # 🧠 1. KHỞI TẠO HOẶC LẤY LẠI LỊCH SỬ CHAT TỪ SESSION CỦA NGƯỜI DÙNG
            # Nếu người dùng mới chat câu đầu tiên, tạo một mảng trống []
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []
            
            # Lấy lịch sử cũ ra
            history = request.session['chat_history']

            # 🎭 2. ĐỊNH HÌNH TÍNH CÁCH (SYSTEM PROMPT) CHO GEMINI
            system_instruction = (
                "Bạn là một chuyên gia tư vấn bất động sản tại Việt Nam. "
                "Hãy trả lời khách hàng một cách lịch sự, ngắn gọn, chuyên nghiệp. "
                "Chỉ trả lời các vấn đề liên quan đến mua bán, thuê nhà, luật đất đai, phong thủy nhà ở. "
                "Dưới đây là lịch sử cuộc trò chuyện và câu hỏi mới của khách hàng, hãy dựa vào đó để trả lời tiếp nối một cách logic.\n\n"
            )

            # 🔄 3. GỘP LỊCH SỬ CHAT CŨ VÀO NỘI DUNG GỬI LÊN GOOGLE
            full_context = system_instruction
            for chat in history:
                full_context += f"Khách hàng: {chat['user']}\n"
                full_context += f"AI Chuyên gia: {chat['bot']}\n"
            
            # Thêm câu hỏi mới nhất hiện tại của người dùng vào cuối cùng
            full_context += f"Khách hàng: {user_message}\nAI Chuyên gia:"

            # Gọi Gemini tạo câu trả lời dựa trên toàn bộ ngữ cảnh từ trước đến nay
            bot_reply = get_gemini_reply(full_context)
            if not bot_reply.strip():
                bot_reply = build_fallback_reply(user_message)

            # 💾 4. LƯU CÂU CHAT MỚI NÀY VÀO LỊCH SỬ SESSION ĐỂ LẦN SAU DÙNG TIẾP
            history.append({
                'user': user_message,
                'bot': bot_reply
            })
            
            # Giới hạn chỉ nhớ 10 câu gần nhất để tránh đầy bộ nhớ và chậm AI
            if len(history) > 10:
                history.pop(0)

            # Cập nhật lại session và đánh dấu đã thay đổi để Django lưu vào Database
            request.session['chat_history'] = history
            request.session.modified = True
            
            # Trả kết quả về cho giao diện web hiển thị
            return JsonResponse({'reply': bot_reply})
            
        except Exception as e:
            print(f"Lỗi AI: {str(e)}")
            fallback_reply = build_fallback_reply(user_message)
            return JsonResponse({'reply': fallback_reply})
            
    return JsonResponse({'error': 'Lỗi phương thức kết nối'})
def predict_price(request):
    if request.method == 'POST':
        # 1. Nhận các thông số từ Form giao diện HTML gửi lên
        dien_tich = float(request.POST.get('dien_tich', 0))
        so_phong_ngu = int(request.POST.get('so_phong_ngu', 1))
        so_phong_tam = int(request.POST.get('so_phong_tam', 1))
        khu_vuc = request.POST.get('khu_vuc', 'Hà Nội')
        loai_nha = request.POST.get('loai_nha', 'Nhà phố')
        vi_tri = request.POST.get('vi_tri', 'Mặt tiền')
        nam_xay_dung = int(request.POST.get('nam_xay_dung', 2025))

        # 2. Tạo DataFrame khớp HOÀN TOÀN với các thuộc tính bộ não AI mới đã học
        # Chú ý: Tên các cột ở đây phải giống hệt các cột tập lệnh train_bot.py vừa học!
        input_data = pd.DataFrame([{
            'dien_tich': dien_tich,
            'so_phong_ngu': so_phong_ngu,
            'so_phong_tam': so_phong_tam,
            'khu_vực': khu_vuc,    # Chữ 'vực' có dấu đúng chuẩn cấu hình học của Bot
            'loai_nha': loai_nha,
            'vi_tri': vi_tri,
            'nam_xay_dung': nam_xay_dung
        }])

        # 3. Đường dẫn nạp file bộ não AI thành phẩm
        model_path = 'bot_du_doan_nang_cap.pkl'
        
        if os.path.exists(model_path):
            bot_brain = joblib.load(model_path)
            
            # AI thực hiện tính toán giá (Kết quả trả về đơn vị Triệu VND)
            predicted_price_raw = bot_brain.predict(input_data)[0]
            
            # --- TÍNH TOÁN CÁC TIÊU CHÍ HIỂN THỊ RA MÀN HÌNH ---
            estimated_price = round(predicted_price_raw, 1) 
            
            # Khoảng giá thấp nhất - cao nhất (Biên độ an toàn 8%)
            min_price = round(estimated_price * 0.92, 1)
            max_price = round(estimated_price * 1.08, 1)
            
            # Tính Đơn giá trên mỗi mét vuông (Giá / m²)
            price_per_m2 = round(estimated_price / dien_tich, 2) if dien_tich > 0 else 0
            
            # Phân loại phân khúc nhà dựa trên giá trị
            if estimated_price < 2000:
                segment = "Nhà giá rẻ (Phù hợp thu nhập trung bình)"
            elif 2000 <= estimated_price <= 6000:
                segment = "Nhà trung cấp (Phân khúc phổ thông phổ biến)"
            else:
                segment = "Nhà cao cấp (Bất động sản giá trị cao)"

            # Đóng gói dữ liệu để truyền ra file hiển thị HTML
            context = {
                'estimated_price': f"{estimated_price:,} Triệu VND",
                'min_price': f"{min_price:,} Triệu VND",
                'max_price': f"{max_price:,} Triệu VND",
                'price_per_m2': f"{price_per_m2:,} Triệu/m²",
                'segment': segment,
                'input_stats': {
                    'dien_tich': dien_tich,
                    'khu_vuc': khu_vuc,
                    'loai_nha': loai_nha
                }
            }
            return render(request, 'properties/predict_result.html', context)
        else:
            return render(request, 'properties/predict_result.html', {'error': 'Hệ thống chưa nạp được file bot_du_doan_nang_cap.pkl!'})

    return render(request, 'properties/predict.html')