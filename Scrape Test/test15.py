import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import csv
import time
from bs4 import BeautifulSoup

START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

def plausible_author(val):
    if not val: return False
    if len(val) > 40: return False
    badwords = ["Источник", "Дата", "Заглавие", "Номер выпуска", "Best.ru", "http", "www.", "Премия"]
    if any(bad in val for bad in badwords): return False
    if any(char.isdigit() for char in val): return False
    return True

def plausible_source(val):
    if not val: return False
    badwords = ["Дата", "Заглавие", "Автор", "Номер выпуска", "Best.ru", "Премия"]
    if any(bad in val for bad in badwords): return False
    return True

def plausible_title(val):
    if not val: return False
    badwords = ["Источник", "Дата", "Автор", "Номер выпуска", "Best.ru", "Премия"]
    if any(bad in val for bad in badwords): return False
    return True

def extract_author_from_text(text):
    match = re.search(r'Автор[:\s]*([^\n\r]+)', text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        candidate = re.split(r'(Источник|Дата|Заглавие|Номер выпуска|Best\.ru|Премия)', candidate)[0].strip()
        if plausible_author(candidate):
            return candidate
    return ""

def extract_from_fb_frame(driver, fallback_title=None):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    data = {'source':'','date':'','author':'','title':'','body':''}

    pres = soup.find_all('pre')
    if pres:
        all_text = []
        for pre_html in pres:
            all_text.append(pre_html.get_text("\n"))
        full_text = "\n".join(all_text)
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if line.startswith('Источник:'):
                val = line.replace('Источник:', '').strip()
                data['source'] = val if plausible_source(val) else ""
            elif line.startswith('Дата выпуска:'):
                val = line.replace('Дата выпуска:', '').strip()
                data['date'] = val if val else ""
            elif line.startswith('Заглавие:'):
                val = line.replace('Заглавие:', '').strip()
                data['title'] = val if plausible_title(val) else ""
                data['body'] = '\n'.join(lines[i+1:]).strip()
                break
        data['author'] = extract_author_from_text(full_text)
        if data['title'] or data['body']:
            return data

    meta_font = None
    for font in soup.find_all('font'):
        if 'Источник:' in font.get_text():
            meta_font = font
            break
    if meta_font:
        for br in meta_font.find_all("br"):
            br.replace_with("\n")
        lines = [line.strip() for line in meta_font.get_text("\n").split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if line.startswith('Источник:'):
                val = line.replace('Источник:', '').strip()
                data['source'] = val if plausible_source(val) else ""
            elif line.startswith('Дата выпуска:'):
                val = line.replace('Дата выпуска:', '').strip()
                data['date'] = val if val else ""
            elif line.startswith('Заглавие:'):
                val = line.replace('Заглавие:', '').strip()
                data['title'] = val if plausible_title(val) else ""
        data['author'] = extract_author_from_text(meta_font.get_text("\n"))
        body_parts = []
        found_meta = False
        found_author = False
        for tag in soup.find_all(['h1', 'p', 'font']):
            if tag == meta_font:
                found_meta = True
                continue
            if not found_meta:
                continue
            if tag.name == 'font' and not found_author:
                found_author = True
                continue
            text = tag.get_text(" ", strip=True)
            if text:
                body_parts.append(text)
        if body_parts:
            data['body'] = "\n".join(body_parts).strip()
        if data['title'] or data['body']:
            return data

    tds = soup.find_all('td')
    max_text = ""
    for td in tds:
        td_html = str(td)
        if 'Источник:' in td_html and 'Заглавие:' in td_html:
            continue
        text = BeautifulSoup(td_html, "html.parser").get_text("\n").strip()
        if len(text) > len(max_text):
            max_text = text
    if max_text:
        data['body'] = max_text.strip()
        data['author'] = extract_author_from_text(max_text)

    if not data['body']:
        text = soup.get_text("\n").strip()
        if text:
            data['body'] = text
            data['author'] = extract_author_from_text(text)

    if not data['title'] and fallback_title:
        data['title'] = fallback_title

    return data

# --- SPEED OPTIMIZATIONS ---
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
# Block images and CSS for speed
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
    "profile.default_content_settings.cookies": 2
}
options.add_experimental_option("prefs", prefs)
service = ChromeService(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 6)  # Keep wait short for speed[10][1]

try:
    driver.get(START_URL)
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "//input[@type='submit' and @value='Ich akzeptiere die Benutzungsbedingungen']"))).click()
    wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[1]/td[2]/input"))).send_keys(USERNAME)
    wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[2]/td[2]/input"))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[3]/td/input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/form/table/tbody/tr[3]/td/input"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[3]/tbody/tr/td[2]/table/tbody/tr[2]/td/div[1]/a"))).click()
    ta = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
    ta.clear()
    ta.send_keys('"Кирилл Дмитриев"')
    xpaths_to_click = [
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[4]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[8]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[12]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[15]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[16]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[17]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[1]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[11]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[10]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[3]",
    ]
    for xpath in xpaths_to_click:
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", el)
            el.click()
        except Exception:
            pass
    dp = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
    dp.clear(); dp.send_keys("01.01.2010")
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
    driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
    search_btn.click()
    csv_file = open('output.csv', 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(csv_file, fieldnames=['source', 'date', 'author', 'title', 'body', 'url'])
    writer.writeheader()
    time.sleep(0.5)
    cat_xpath = (
        "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
        "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
    )
    next_page_xpath = "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[3]/td/table/tbody/tr/td[2]/a[2]"

    while True:
        categories = driver.find_elements(By.XPATH, cat_xpath)
        if not categories:
            break
        for cat_index in range(len(categories)):
            categories = driver.find_elements(By.XPATH, cat_xpath)
            if cat_index >= len(categories):
                break
            cat_link = categories[cat_index]
            cat_link_text = cat_link.text.strip()
            if "pdf" in cat_link_text.lower() or "архив" in cat_link_text.lower():
                continue
            cat_link.click()
            time.sleep(0.1)
            category_page_num = 1
            pages_scrolled = 1
            while True:
                entry_xpath = (
                    "/html/body/table/tbody/tr[5]/td/table/tbody/tr/td/form/table[4]"
                    "/tbody/tr/td/dt/a"
                )
                entries = driver.find_elements(By.XPATH, entry_xpath)
                if not entries:
                    break
                for entry_index in range(len(entries)):
                    entries = driver.find_elements(By.XPATH, entry_xpath)
                    entry = entries[entry_index]
                    entry_text = entry.text
                    article_url = entry.get_attribute("href")
                    entry.click()
                    time.sleep(0.05)
                    try:
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "fb")))
                    except TimeoutException:
                        # SKIP this doc if frame doesn't load quickly, move on immediately[2][5]
                        driver.switch_to.default_content()
                        driver.back()
                        continue
                    data = extract_from_fb_frame(driver, fallback_title=entry_text)
                    data['url'] = article_url
                    writer.writerow(data)
                    driver.switch_to.default_content()
                    driver.back()
                    time.sleep(0.05)
                category_page_num += 1
                next_cat_page_xpath = f"/html/body/table/tbody/tr[5]/td/table/tbody/tr/td/form/table[5]/tbody/tr/td/table/tbody/tr/td[5]/a[{category_page_num}]"
                short_wait = WebDriverWait(driver, 1)
                try:
                    next_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, next_cat_page_xpath)))
                    next_button.click()
                    pages_scrolled += 1
                    time.sleep(0.1)
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                    break
            for _ in range(pages_scrolled):
                driver.back()
                time.sleep(0.05)
        try:
            next_link = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_xpath)))
            next_link.click()
            time.sleep(0.2)
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
            break
finally:
    try:
        csv_file.close()
    except Exception:
        pass
    driver.quit()
