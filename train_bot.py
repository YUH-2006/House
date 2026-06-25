import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# 1. Giả lập tập dữ liệu lớn và chi tiết hơn (Huy có thể thay bằng file Excel thật)
data = {
    'dien_tich': [50, 80, 120, 45, 60, 200, 35, 90],
    'so_phong_ngu': [2, 3, 4, 1, 2, 5, 1, 3],
    'so_phong_tam': [1, 2, 3, 1, 2, 4, 1, 2],
    'khu_vực': ['Quận 1', 'Quận 7', 'Cầu Giấy', 'Quận 1', 'Quận 7', 'Cầu Giấy', 'Quận 1', 'Cầu Giấy'],
    'loai_nha': ['Chung cư', 'Nhà phố', 'Biệt thự', 'Chung cư', 'Nhà phố', 'Biệt thự', 'Chung cư', 'Nhà phố'],
    'vi_tri': ['Hẻm', 'Mặt tiền', 'Mặt tiền', 'Hẻm', 'Hẻm', 'Mặt tiền', 'Hẻm', 'Mặt tiền'],
    'nam_xay_dung': [2020, 2018, 2022, 2015, 2019, 2024, 2010, 2021],
    'gia_ban': [2500, 6000, 15000, 1800, 3500, 32000, 1400, 7200] # Đơn vị: Triệu VND
}

df = pd.DataFrame(data)

# 2. Chia thuộc tính (X) và Nhãn giá trị (y)
X = df.drop(columns=['gia_ban'])
y = df['gia_ban']

# 3. Xử lý chuẩn hóa dữ liệu: Chữ (Categorical) tự động chuyển thành Số thông qua Pipeline
numeric_features = ['dien_tich', 'so_phong_ngu', 'so_phong_tam', 'nam_xay_dung']
categorical_features = ['khu_vực', 'loai_nha', 'vi_tri']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# 4. Tạo chuỗi liên kết thuật toán với Random Forest
bot_model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# 5. Huấn luyện mô hình
bot_model.fit(X, y)

# 6. Lưu bộ não đa năng này lại
joblib.dump(bot_model, 'bot_du_doan_nang_cap.pkl')
print("🤖 Bộ não Trợ lý AI nâng cấp đã học xong thành công!")