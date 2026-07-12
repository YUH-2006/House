import sys
import io
import joblib
import pandas as pd

# Set UTF-8 encoding
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

model = joblib.load('bot_du_doan_nang_cap.pkl')

sample = pd.DataFrame([{
    'dien_tich': 80.0,
    'so_phong_ngu': 3,
    'so_phong_tam': 2,
    'khu_vực': 'Hồ Chí Minh',
    'loai_nha': 'Nhà phố',
    'vi_tri': 'Mặt tiền',
    'nam_xay_dung': 2020
}])

print('Sample input:', sample.to_dict(orient='records'))
print('Predicted (Triệu VND):', model.predict(sample)[0])
