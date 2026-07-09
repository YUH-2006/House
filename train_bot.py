import pandas as pd
import numpy as np
import re
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

# Cấu hình danh sách các file dữ liệu Huy muốn nạp vào cùng lúc
csv_filename = 'kaggle_housing_data.csv,dn.csv,hcm.csv,hn.csv'

# Tách chuỗi thành mảng các file riêng biệt
csv_files = [f.strip() for f in csv_filename.split(',')]

# Kiểm tra sự tồn tại của tất cả các file trước khi chạy
for filename in csv_files:
    if not os.path.exists(filename):
        print(f"❌ LỖI: Không tìm thấy file '{filename}' trong thư mục dự án!")
        print("👉 Huy hãy chắc chắn đã copy cả 4 file này vào cùng cấp với file manage.py nhé.")
        exit()

# Hàm quét chữ tiếng Việt thông minh dành riêng cho file gốc kaggle_housing_data.csv
def extract_features_from_desc(row):
    desc = str(row['description']).lower() if pd.notnull(row['description']) else ""
    name = str(row['name']).lower() if pd.notnull(row['name']) else ""
    text = name + " " + desc
    
    dien_tich = np.nan
    match_dt = re.search(r'(\d+[\.,]?\d*)\s*(m2|m²)', text)
    if match_dt:
        dien_tich = float(match_dt.group(1).replace(',', '.'))
        
    phong_ngu = 2 
    match_pn = re.search(r'(\d+)\s*(pn|phòng ngủ)', text)
    if match_pn:
        phong_ngu = min(int(match_pn.group(1)), 8)
        
    gia_vnd = np.nan
    match_ty = re.search(r'(\d+[\.,]?\d*)\s*(tỷ|ti)', text)
    match_tr = re.search(r'(\d+[\.,]?\d*)\s*(triệu|tr)', text)
    
    if match_ty:
        gia_vnd = float(match_ty.group(1).replace(',', '.')) * 1000 
    elif match_tr:
        gia_vnd = float(match_tr.group(1).replace(',', '.'))
        
    return pd.Series([dien_tich, phong_ngu, gia_vnd])

# Mảng trung gian chứa dữ liệu sau khi chuẩn hóa của từng file
list_of_dfs = []

print("⏳ 1. Bắt đầu đọc và phân tách cấu trúc hàng loạt file Kaggle...")

for filename in csv_files:
    print(f"📦 Đang xử lý file: {filename} ...")
    raw_df = pd.read_csv(filename, low_memory=False)
    df_clean = pd.DataFrame()
    
    # 🔎 TRƯỜNG HỢP 1: Nếu là các file thuê nhà (dn.csv, hcm.csv, hn.csv) có sẵn cột acreage
    if 'acreage' in raw_df.columns and 'price' in raw_df.columns:
        df_clean['dien_tich'] = pd.to_numeric(raw_df['acreage'], errors='coerce')
        
        # Đọc số phòng ngủ từ tiêu đề (nếu có), không có thì mặc định là 1 hoặc 2
        def parse_phong(title):
            text = str(title).lower()
            match = re.search(r'(\d+)\s*(pn|phòng ngủ|phòng)', text)
            return min(int(match.group(1)), 8) if match else 2
        
        df_clean['so_phong_ngu'] = raw_df['title'].apply(parse_phong) if 'title' in raw_df.columns else 2
        df_clean['so_phong_tam'] = 1 
        
        # Tự động gắn Tỉnh/Thành phố dựa vào tên file dữ liệu thuê
        if 'hn' in filename:
            df_clean['khu_vực'] = 'Hà Nội'
        elif 'hcm' in filename:
            df_clean['khu_vực'] = 'Hồ Chí Minh'
        elif 'dn' in filename:
            df_clean['khu_vực'] = 'Đà Nẵng'
        else:
            df_clean['khu_vực'] = 'Hà Nội'
            
        df_clean['loai_nha'] = 'Chung cư/Phòng trọ'
        df_clean['vi_tri'] = 'Trong ngõ'
        df_clean['nam_xay_dung'] = 2026
        
        # MẸO AI: Quy đổi giá thuê (Triệu/tháng) sang giá trị tài sản tương đương (x300 lần) để tránh lệch pha với file Bán
        df_clean['gia_ban'] = pd.to_numeric(raw_df['price'], errors='coerce') * 300

    # 🔎 TRƯỜNG HỢP 2: Nếu là file Bán nhà gốc kaggle_housing_data.csv cần bóc tách từ description
    else:
        raw_df[['dien_tich', 'so_phong_ngu', 'gia_ban']] = raw_df.apply(extract_features_from_desc, axis=1)
        
        df_clean['dien_tich'] = raw_df['dien_tich']
        df_clean['so_phong_ngu'] = raw_df['so_phong_ngu']
        df_clean['so_phong_tam'] = 1 
        df_clean['khu_vực'] = raw_df['province_name'].fillna('Hà Nội').astype(str)
        df_clean['loai_nha'] = raw_df['property_type_name'].fillna('Nhà phố').astype(str)
        df_clean['vi_tri'] = 'Mặt tiền' 
        df_clean['nam_xay_dung'] = 2026
        df_clean['gia_ban'] = raw_df['gia_ban']

    # Loại bỏ dữ liệu khuyết và rác của file hiện tại, rồi thêm vào mảng gộp
    df_clean = df_clean.dropna(subset=['gia_ban', 'dien_tich'])
    df_clean = df_clean[(df_clean['gia_ban'] > 10) & (df_clean['dien_tich'] > 10)]
    list_of_dfs.append(df_clean)

# =========================================================================
# 🔥 TIẾN HÀNH GỘP TẤT CẢ CÁC DATA FRAME LẠI THÀNH MỘT BỘ TRI THỨC DUY NHẤT
# =========================================================================
combined_df = pd.concat(list_of_dfs, ignore_index=True)
print(f"\n⚡ Đã gộp dữ liệu thành công! Tổng số lượng tin đăng thu thập được: {len(combined_df)} dòng.")

# Giới hạn lấy mẫu ngẫu nhiên để thuật toán học nhanh, không treo máy
sample_size = min(len(combined_df), 30000)
df_final = combined_df.sample(n=sample_size, random_state=42)

X = df_final.drop(columns=['gia_ban'])
y = df_final['gia_ban']

print(f"🤖 2. Thiết lập bộ tiền xử lý ma trận cho {sample_size} mẫu đa nguồn...")
numeric_features = ['dien_tich', 'so_phong_ngu', 'so_phong_tam', 'nam_xay_dung']
categorical_features = ['khu_vực', 'loai_nha', 'vi_tri']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

bot_model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1))
])

print("🔥 3. Bot AI đang thực hiện học tập quy luật thị trường gộp (Bán & Thuê)...")
bot_model.fit(X, y)

# Xuất file bộ não thành phẩm tối cao nạp cho Django
joblib.dump(bot_model, 'bot_du_doan_nang_cap.pkl')
print("\n✅ THÀNH CÔNG RỰC RỠ: Bộ não AI đã hấp thụ toàn bộ tri thức từ cả 4 file Kaggle cùng lúc!")