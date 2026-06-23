import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# 1. Tạo dữ liệu giả lập để dạy cho Bot (Sau này có dữ liệu thật bạn thay vào nhé)
data = {
    'dien_tich': [40, 50, 60, 80, 100, 120, 150, 200],
    'so_phong': [1, 2, 2, 3, 3, 4, 4, 5],
    'gia_trieu_dong': [1200, 1600, 2000, 2800, 3500, 4200, 5500, 7500] 
}

df = pd.DataFrame(data)

# 2. Phân chia đầu vào (X) và đầu ra cần đoán (y)
X = df[['dien_tich', 'so_phong']]
y = df['gia_trieu_dong']

# 3. Khởi tạo thuật toán và cho Bot học (Fit)
bot = LinearRegression()
bot.fit(X, y)

# 4. Xuất con bot đã học xong thành file 'bot_du_doan.pkl'
joblib.dump(bot, 'bot_du_doan.pkl')
print("Bot đã học xong và lưu thành file bot_du_doan.pkl!")