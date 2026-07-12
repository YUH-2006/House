import os
import re
import sys
import io

# Set UTF-8 encoding for stdout
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

csv_filename = "kaggle_housing_data.csv,dn.csv,hcm.csv,hn.csv,nhatot_data.csv"
csv_files = [f.strip() for f in csv_filename.split(",") if f.strip()]


def normalize_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    text = text.replace("đ", "").replace("vnd", "")

    match_ty = re.search(r"(\d+[\.,]?\d*)\s*(tỷ|ty)", text)
    match_tr = re.search(r"(\d+[\.,]?\d*)\s*(triệu|tr)", text)
    if match_ty:
        return float(match_ty.group(1).replace(",", ".")) * 1000
    if match_tr:
        return float(match_tr.group(1).replace(",", "."))

    try:
        number = float(re.sub(r"[^0-9.,-]", "", text).replace(".", "").replace(",", "."))
    except Exception:
        return np.nan

    if abs(number) >= 1_000_000:
        return number / 1_000_000
    return number


def extract_features_from_desc(row):
    desc = ""
    name = ""
    for key in ("description", "desc", "mo_ta", "detail", "title", "name"):
        if key in row and pd.notna(row[key]):
            value = str(row[key])
            if key in {"title", "name"}:
                name = value.lower()
            else:
                desc = value.lower()
            break

    text = f"{name} {desc}".lower()

    dien_tich = np.nan
    match_dt = re.search(r"(\d+[\.,]?\d*)\s*(m2|m²|mét vuông)", text)
    if match_dt:
        dien_tich = float(match_dt.group(1).replace(",", "."))

    phong_ngu = 2
    match_pn = re.search(r"(\d+)\s*(pn|phòng ngủ|phòng)", text)
    if match_pn:
        phong_ngu = min(int(match_pn.group(1)), 8)

    # Trích xuất số phòng tắm nếu có
    so_phong_tam = 1
    match_pt = re.search(r"(\d+)\s*(pt|phòng tắm|toilet|wc)", text)
    if match_pt:
        so_phong_tam = min(int(match_pt.group(1)), 6)

    gia_vnd = np.nan
    match_ty = re.search(r"(\d+[\.,]?\d*)\s*(tỷ|ti)", text)
    match_tr = re.search(r"(\d+[\.,]?\d*)\s*(triệu|tr)", text)

    if match_ty:
        gia_vnd = float(match_ty.group(1).replace(",", ".")) * 1000
    elif match_tr:
        gia_vnd = float(match_tr.group(1).replace(",", "."))

    return pd.Series([dien_tich, phong_ngu, so_phong_tam, gia_vnd])


def standardize_loai_nha(loai_nha):
    """Chuẩn hóa giá trị loai_nha để khớp với form"""
    loai_nha = str(loai_nha).lower().strip()
    if any(keyword in loai_nha for keyword in ['nhà phố', 'nhà']):
        return 'Nhà phố'
    elif any(keyword in loai_nha for keyword in ['chung cư', 'căn hộ', 'phòng trọ']):
        return 'Chung cư'
    elif any(keyword in loai_nha for keyword in ['biệt thự', 'nhà liền kề']):
        return 'Biệt thự'
    elif any(keyword in loai_nha for keyword in ['đất']):
        return 'Đất nền'
    else:
        return 'Nhà phố'  # Mặc định

def load_external_listing_csv(path, source_name="nhatot_data.csv"):
    if not os.path.exists(path):
        return pd.DataFrame()

    raw_df = pd.read_csv(path, low_memory=False)
    if raw_df.empty:
        return pd.DataFrame()

    df = pd.DataFrame()
    title_col = next((c for c in ["title", "tieu_de", "name"] if c in raw_df.columns), None)
    price_col = next((c for c in ["price", "gia"] if c in raw_df.columns), None)
    area_col = next((c for c in ["area", "dien_tich", "acreage"] if c in raw_df.columns), None)

    if title_col is None or price_col is None:
        return pd.DataFrame()

    df["title"] = raw_df[title_col].fillna("")
    df["dien_tich"] = pd.to_numeric(raw_df[area_col], errors="coerce") if area_col else np.nan
    df["gia_ban"] = raw_df[price_col].apply(normalize_price)

    def parse_phong(text):
        match = re.search(r"(\d+)\s*(pn|phòng ngủ|phòng)", str(text).lower())
        return min(int(match.group(1)), 8) if match else 2

    def parse_pt(text):
        match = re.search(r"(\d+)\s*(pt|phòng tắm|toilet|wc)", str(text).lower())
        return min(int(match.group(1)), 6) if match else 1

    def parse_area(text):
        match = re.search(r"(\d+[\.,]?\d*)\s*(m2|m²|mét vuông)", str(text).lower())
        return float(match.group(1).replace(",", ".")) if match else np.nan

    df["so_phong_ngu"] = df["title"].apply(parse_phong)
    df["so_phong_tam"] = df["title"].apply(parse_pt)
    if df["dien_tich"].isna().all():
        df["dien_tich"] = df["title"].apply(parse_area)

    # nếu chưa có giá trị phòng tắm, đảm bảo tối thiểu 1
    df["so_phong_tam"] = df.get("so_phong_tam", pd.Series([1] * len(df)))
    df["khu_vực"] = "Hồ Chí Minh"
    df["loai_nha"] = "Nhà phố"  # Will standardize later
    df["vi_tri"] = "Mặt tiền"
    df["nam_xay_dung"] = 2025

    if "nhatot" in source_name.lower() or "chotot" in source_name.lower():
        df["khu_vực"] = "Hồ Chí Minh"

    df = df.dropna(subset=["gia_ban", "dien_tich"])
    df = df[(df["gia_ban"] > 10) & (df["dien_tich"] > 10)]
    return df


def build_training_frame(files=None):
    files_to_use = files or csv_files
    list_of_dfs = []

    print('[1] Bắt đầu đọc và chuẩn hóa dữ liệu từ nhiều nguồn...')
    for filename in files_to_use:
        print(f'Đang xử lý file: {filename} ...')
        if not os.path.exists(filename):
            print(f'Không tìm thấy file \'{filename}\', bỏ qua.')
            continue

        if filename.lower() == "nhatot_data.csv":
            df_clean = load_external_listing_csv(filename, source_name=filename)
            if not df_clean.empty:
                list_of_dfs.append(df_clean)
            continue

        raw_df = pd.read_csv(filename, low_memory=False)
        df_clean = pd.DataFrame()

        if "acreage" in raw_df.columns and "price" in raw_df.columns:
            df_clean["dien_tich"] = pd.to_numeric(raw_df["acreage"], errors="coerce")

            def parse_phong(title):
                text = str(title).lower()
                match = re.search(r"(\d+)\s*(pn|phòng ngủ|phòng)", text)
                return min(int(match.group(1)), 8) if match else 2

            df_clean["so_phong_ngu"] = raw_df["title"].apply(parse_phong) if "title" in raw_df.columns else 2
            df_clean["so_phong_tam"] = 1

            if "hn" in filename:
                df_clean["khu_vực"] = "Hà Nội"
            elif "hcm" in filename:
                df_clean["khu_vực"] = "Hồ Chí Minh"
            elif "dn" in filename:
                df_clean["khu_vực"] = "Đà Nẵng"
            else:
                df_clean["khu_vực"] = "Hà Nội"

            df_clean["loai_nha"] = "Chung cư"
            df_clean["vi_tri"] = "Trong ngõ"
            df_clean["nam_xay_dung"] = 2026
            df_clean["gia_ban"] = pd.to_numeric(raw_df["price"], errors="coerce") * 300
        else:
            parsed = raw_df.apply(extract_features_from_desc, axis=1)
            # extract_features_from_desc now returns (dien_tich, so_phong_ngu, so_phong_tam, gia_ban)
            raw_df[["dien_tich", "so_phong_ngu", "so_phong_tam", "gia_ban"]] = parsed

            df_clean["dien_tich"] = raw_df["dien_tich"]
            df_clean["so_phong_ngu"] = raw_df["so_phong_ngu"]
            df_clean["so_phong_tam"] = raw_df["so_phong_tam"].fillna(1)
            df_clean["khu_vực"] = raw_df.get("province_name", pd.Series(["Hà Nội"] * len(raw_df))).fillna("Hà Nội").astype(str)
            df_clean["loai_nha"] = raw_df.get("property_type_name", pd.Series(["Nhà phố"] * len(raw_df))).fillna("Nhà phố").astype(str)
            df_clean["vi_tri"] = "Mặt tiền"
            df_clean["nam_xay_dung"] = 2026
            df_clean["gia_ban"] = raw_df["gia_ban"]

        df_clean = df_clean.dropna(subset=["gia_ban", "dien_tich"])
        df_clean = df_clean[(df_clean["gia_ban"] > 10) & (df_clean["dien_tich"] > 10)]
        if not df_clean.empty:
            list_of_dfs.append(df_clean)

    if not list_of_dfs:
        raise ValueError("Không có dữ liệu hợp lệ để huấn luyện")

    combined_df = pd.concat(list_of_dfs, ignore_index=True)
    # Chuẩn hóa toàn bộ loai_nha sau khi gộp
    combined_df["loai_nha"] = combined_df["loai_nha"].apply(standardize_loai_nha)
    print(f"\nĐã gộp dữ liệu thành công! Tổng số lượng tin đăng thu thập được: {len(combined_df)} dòng.")
    sample_size = min(len(combined_df), 60000)
    return combined_df.sample(n=sample_size, random_state=42)


def train_model(files=None, output_path="bot_du_doan_nang_cap.pkl"):
    df_final = build_training_frame(files=files)

    X = df_final[["dien_tich", "so_phong_ngu", "so_phong_tam", "khu_vực", "loai_nha", "vi_tri", "nam_xay_dung"]]
    y = df_final["gia_ban"]

    print(f'[2] Thiết lập bộ tiền xử lý ma trận cho {len(df_final)} mẫu đa nguồn...')
    numeric_features = ["dien_tich", "so_phong_ngu", "so_phong_tam", "nam_xay_dung"]
    categorical_features = ["khu_vực", "loai_nha", "vi_tri"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    bot_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=250, max_depth=18, random_state=42, n_jobs=-1)),
        ]
    )

    print('[3] Bot AI đang thực hiện học tập quy luật thị trường gộp (Bán & Thuê) với cấu hình mạnh hơn...')
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    bot_model.fit(X_train, y_train)
    pred_test = bot_model.predict(X_test)
    mae = mean_absolute_error(y_test, pred_test)
    print(f'[4] MAE trên tập test: {mae:.2f} triệu VND')

    joblib.dump(bot_model, output_path)
    print(f'\nTHÀNH CÔNG: Bộ não AI đã được nâng cấp và lưu lại tại {output_path}!')
    return bot_model



if __name__ == "__main__":
    train_model()