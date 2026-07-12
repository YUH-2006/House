import sys
import io
import train_bot

# Configure stdout to use UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    df = train_bot.build_training_frame()
    print('\n=== Unique values for khu_vực ===')
    print(df['khu_vực'].value_counts().head(20))  # Top 20
    print('\n=== Unique values for loai_nha ===')
    print(df['loai_nha'].value_counts())
    print('\n=== Unique values for vi_tri ===')
    print(df['vi_tri'].value_counts())
    print('\n=== Unique values for nam_xay_dung ===')
    print(df['nam_xay_dung'].value_counts())
except Exception as e:
    print('ERROR:', e)
    import traceback
    traceback.print_exc()
