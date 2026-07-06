import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

csv_filename = 'kaggle_housing_data.csv'

if not os.path.exists(csv_filename):
    print(f"❌ LỖI: Không tìm thấy file '{csv_filename}' trong thư mục dự án!")
    print("👉 Huy hãy giải nén file từ Kaggle, đổi tên thành 'kaggle_housing_data.csv' rồi bỏ vào cùng cấp với file manage.py nhé.")
    exit()

print(f"⏳ 1. Đang đọc dữ liệu thực tế từ Kaggle Việt Nam ({csv_filename})...")
# Đọc file CSV (Sử dụng thêm error_bad_lines hoặc cấu hình bộ nhớ nếu file quá lớn)
raw_df = pd.read_csv(csv_filename, low_memory=False)

print("⚙️ 2. Đang tiến hành lọc và chuẩn hóa dữ liệu theo Form hệ thống...")

# Tạo một DataFrame sạch để huấn luyện mô hình
df = pd.DataFrame()

# =========================================================================
# ĐOẠN ĐỒNG BỘ CỘT: Ánh xạ cột từ file Kaggle TiniX sang biến của Bot.
# (Nếu file CSV thực tế có tên cột viết hoa/thường khác biệt, Huy chỉ cần sửa tên trong ngoặc vuông)
# =========================================================================
try:
    df['dien_tich'] = pd.to_numeric(raw_df['acreage'], errors='coerce')      # Diện tích (m²)
    df['so_phong_ngu'] = pd.to_numeric(raw_df['bedroom'], errors='coerce')    # Số phòng ngủ
    df['so_phong_tam'] = pd.to_numeric(raw_df['bathroom'], errors='coerce')  # Số phòng tắm
    df['khu_vực'] = raw_df['province'].astype(str)                           # Tỉnh / Thành phố
    df['loai_nha'] = raw_df['property_type'].astype(str)                     # Loại hình BĐS (Nhà phố/Chung cư...)
    df['vi_tri'] = raw_df['legal_status'].astype(str)                        # Trạng thái pháp lý hoặc vị trí hẻm/mặt tiền
    df['nam_xay_dung'] = 2025 # Mặc định năm theo mốc dữ liệu nếu file không có cột năm
    df['gia_ban'] = pd.to_numeric(raw_df['price'], errors='coerce')          # Giá bán gốc (Triệu VND hoặc VND)
except KeyError as e:
    print(f"❌ LỖI: File CSV của bạn không khớp tên cột! Thiếu cột: {e}")
    print("👉 Hãy mở file CSV bằng Excel để kiểm tra lại chính xác tiêu đề các cột dữ liệu.")
    exit()

# Làm sạch: Loại bỏ các dòng dữ liệu trống (NaN) hoặc dữ liệu rác (Ví dụ giá bằng 0 hoặc diện tích âm)
df = df.dropna()
df = df[(df['gia_ban'] > 0) & (df['dien_tich'] > 0)]

# Giới hạn số lượng mẫu huấn luyện nếu máy của bạn bị chậm (Bộ dữ liệu gốc có tới 1 triệu dòng)
if len(df) > 50000:
    print("⚡ Dữ liệu quá lớn (1 triệu dòng), Bot đang lấy ngẫu nhiên 50,000 dòng chất lượng nhất để tránh treo máy...")
    df = df.sample(n=50000, random_state=42)

# Tách dữ liệu đầu vào và đầu ra
X = df.drop(columns=['gia_ban'])
y = df['gia_ban']

print("🤖 3. Thiết lập ma trận Pipeline mã hóa ngôn ngữ tự động...")
numeric_features = ['dien_tich', 'so_phong_ngu', 'so_phong_tam', 'nam_xay_dung']
categorical_features = ['khu_vực', 'loai_nha', 'vi_tri']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Sử dụng thuật toán Random Forest tối ưu cho dữ liệu bảng biểu lớn
bot_model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1))
])

print("🔥 4. Bot đang thực hiện học tập và phân tích dữ liệu thị trường Việt Nam...")
bot_model.fit(X, y)

# Ghi đè file bộ não mới phục vụ cho web Django
joblib.dump(bot_model, 'bot_du_doan_nang_cap.pkl')
print("\n✅ HUÂN LUYỆN THÀNH CÔNG!")
print("👉 Bộ não 'bot_du_doan_nang_cap.pkl' đã sở hữu kinh nghiệm thực tế từ 1 triệu bất động sản Kaggle!")