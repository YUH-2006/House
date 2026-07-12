import sys
import io
import train_bot

# Configure stdout to use UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Build training frame using available CSV files (may sample up to 60000 rows)
try:
    df = train_bot.build_training_frame()
    print('\n=== DataFrame shape ===')
    print(df.shape)
    print('\n=== dtypes ===')
    print(df.dtypes)
    print('\n=== columns ===')
    print(list(df.columns))
    print('\n=== sample rows ===')
    print(df.head(5).to_dict(orient='records'))
except Exception as e:
    print('ERROR while building training frame:', e)
    import traceback
    traceback.print_exc()
