import csv
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.nhatot.com/mua-ban-bat-dong-san"
OUTPUT = "nhatot_data.csv"


def build_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def extract_price(text):
    m = re.search(r"(\d[\d\.,]*)\s*(tỷ|triệu|tr)", text.lower())
    if not m:
        return ""
    value = float(m.group(1).replace('.', '').replace(',', '.'))
    unit = m.group(2).lower()
    if unit in {'tỷ', 'ty'}:
        return round(value * 1000 * 1000000, 0)
    return round(value * 1000000, 0)


def scrape_current_page(driver):
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main a[href*='.htm']")))
    items = driver.execute_script("""
        const seen = new Set();
        const results = [];
        const links = Array.from(document.querySelectorAll('main a[href*=".htm"], main button[href], main [href*=".htm"]'));
        for (const el of links) {
            const href = el.getAttribute('href') || '';
            const text = (el.innerText || '').replace(/\s+/g, ' ').trim();
            if (!href || !text) continue;
            const full = href + ' :: ' + text;
            if (seen.has(full)) continue;
            seen.add(full);
            if (/tỷ|triệu|tr\/m²|m²|m2|giá|diện tích/i.test(text) || /\.htm/.test(href)) {
                results.push({href, text});
            }
        }
        return results.slice(0, 50);
    """)
    return items


def save_csv(items, output):
    with open(output, 'w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['title', 'url', 'price'])
        for item in items:
            writer.writerow([item['text'], 'https://www.nhatot.com' + item['href'], extract_price(item['text'])])


def main():
    driver = build_driver()
    try:
        driver.get(URL)
        time.sleep(6)
        items = scrape_current_page(driver)
        save_csv(items, OUTPUT)
        print(f'Đã lưu {len(items)} tin vào {OUTPUT}')
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
