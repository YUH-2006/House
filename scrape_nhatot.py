import argparse
import csv
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

URL = "https://www.nhatot.com/mua-ban-bat-dong-san"
OUTPUT = "nhatot_data.csv"


def detect_profile_path():
    candidates = []
    user = os.getenv("USERNAME") or os.getenv("USER") or ""
    if user:
        candidates.append(Path(rf"C:\Users\{user}\AppData\Local\Google\Chrome\User Data"))
    candidates.extend([
        Path(r"C:\Users\Huy\AppData\Local\Google\Chrome\User Data"),
        Path(r"C:\Program Files\Google\Chrome\Application"),
    ])
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def build_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    profile_dir = detect_profile_path()
    if profile_dir:
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")
        print(f"Đang dùng profile Chrome: {profile_dir}")
    else:
        print("Không tìm thấy profile Chrome, sẽ dùng instance sạch.")

    try:
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as exc:
        print("Chrome khởi động thất bại, thử Edge:", exc)
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        return webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)


def extract_text(el):
    try:
        return el.text.strip()
    except Exception:
        return ""


def extract_price(text):
    match = re.search(r"(\d[\d\.,]*)\s*(tỷ|triệu|tr)", text.lower())
    if not match:
        return ""
    value = float(match.group(1).replace(".", "").replace(",", "."))
    unit = match.group(2).lower()
    if unit in {"tỷ", "ty"}:
        return round(value * 1000 * 1000000, 0)
    return round(value * 1000000, 0)


def collect_items(driver):
    items = []
    seen = set()
    selectors = ["a[href*='nhatot.com']", "article a", "div a", "li a"]

    for selector in selectors:
        for link in driver.find_elements(By.CSS_SELECTOR, selector):
            href = (link.get_attribute("href") or "").strip()
            txt = extract_text(link)
            if not href or "nhatot.com" not in href:
                continue
            if len(txt) < 8 or href in seen:
                continue
            if any(k in txt.lower() for k in ["m2", "tỷ", "triệu", "tháng", "giá", "m²"]):
                seen.add(href)
                items.append((txt, href))
            elif any(k in href.lower() for k in ["mua-ban", "ban-"]):
                seen.add(href)
                items.append((txt, href))
    return items


def scrape_nhatot(url=URL, output=OUTPUT, wait_for_manual=False):
    driver = build_driver()
    try:
        driver.get(url)
        time.sleep(6)
        print("Đang mở trang Nhà Tốt...")
        print("Trang hiện tại:", driver.title)

        if "just a moment" in driver.title.lower() or "cloudflare" in driver.page_source.lower():
            print("Cloudflare đang chặn truy cập tự động.")
            if wait_for_manual:
                input("Hãy giải captcha trong trình duyệt rồi nhấn Enter để tiếp tục...")
            else:
                print("Đợi 20 giây để bạn có thể giải captcha thủ công nếu cần...")
                time.sleep(20)

        for _ in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        items = collect_items(driver)
        unique = []
        for txt, href in items:
            if href not in {u[1] for u in unique}:
                unique.append((txt, href))

        with open(output, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["title", "url", "price"])
            for txt, href in unique[:100]:
                writer.writerow([txt, href, extract_price(txt)])

        print(f"Đã lưu {len(unique[:100])} mục vào {output}")
    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=URL)
    parser.add_argument("--output", default=OUTPUT)
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()
    scrape_nhatot(url=args.url, output=args.output, wait_for_manual=args.manual)
