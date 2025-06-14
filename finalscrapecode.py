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

# --- Configuration ---
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

def get_category_next_page_xpath(page_num):
    return f"/html/body/table/tbody/tr[5]/td/table/tbody/tr/td/form/table[5]/tbody/tr/td/table/tbody/tr/td[5]/a[{page_num}]"

def extract_from_pre(pre_htmls):
    all_text = []
    for pre_html in pre_htmls:
        soup = BeautifulSoup(pre_html, "html.parser")
        all_text.append(soup.get_text("\n"))
    full_text = "\n".join(all_text)
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    data = {'source':'','date':'','author':'','title':'','body':''}
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
    for pre_html in pre_htmls:
        pre_soup = BeautifulSoup(pre_html, "html.parser")
        found_author = False
        for tag in pre_soup.descendants:
            if tag.name == 'b' and found_author:
                val = tag.get_text(strip=True)
                data['author'] = val if plausible_author(val) else ""
                break
            if tag.string and 'Автор:' in tag.string:
                found_author = True
        if data['author']:
            break
    return data

def extract_from_fb_frame(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    data = {'source':'','date':'','author':'','title':'','body':''}
    pres = soup.find_all('pre')
    if pres:
        pre_htmls = [str(p) for p in pres]
        return extract_from_pre(pre_htmls)
    meta_font = None
    for font in soup.find_all('font'):
        if 'Источник:' in font.get_text():
            meta_font = font
            break
    if meta_font:
        for br in meta_font.find_all("br"):
            br.replace_with("\n")
        lines = [line.strip() for line in meta_font.get_text("\n").split('\n') if line.strip()]
        for line in lines:
            if line.startswith('Источник:'):
                val = line.replace('Источник:', '').strip()
                data['source'] = val if plausible_source(val) else ""
            elif line.startswith('Дата выпуска:'):
                val = line.replace('Дата выпуска:', '').strip()
                data['date'] = val if val else ""
            elif line.startswith('Автор:'):
                val = line.replace('Автор:', '').strip()
                data['author'] = val if plausible_author(val) else ""
            elif line.startswith('Заглавие:'):
                val = line.replace('Заглавие:', '').strip()
                data['title'] = val if plausible_title(val) else ""
        if not data['author']:
            found_meta = False
            for font in soup.find_all('font'):
                if font == meta_font:
                    found_meta = True
                    continue
                if found_meta:
                    possible_author = font.get_text(strip=True)
                    if plausible_author(possible_author):
                        data['author'] = possible_author
                        break
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
        data['body'] = "\n".join(body_parts).strip()
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
    data['body'] = max_text.strip()
    return data

options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
service = ChromeService(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

try:
    driver.get(START_URL)
    wait.until(
        EC.element_to_be_clickable((By.XPATH,
            "//input[@type='submit' and @value='Ich akzeptiere die Benutzungsbedingungen']"
        ))
    ).click()
    wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[1]/td[2]/input"
    ))).send_keys(USERNAME)
    wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[2]/td[2]/input"
    ))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[3]/td/input"
    ))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/form/table/tbody/tr[3]/td/input"
    ))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[3]/tbody/tr/td[2]/table/tbody/tr[2]/td/div[1]/a"
    ))).click()
    ta = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea"
    )))
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
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]"
    )))
    dp.clear(); dp.send_keys("01.01.2010")
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]"
    )))
    driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
    search_btn.click()
    csv_file = open('output.csv', 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(csv_file, fieldnames=['source', 'date', 'author', 'title', 'body'])
    writer.writeheader()
    time.sleep(1)
    cat_xpath = (
        "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
        "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
    )
    next_page_xpath = "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[3]/td/table/tbody/tr/td[2]/a[2]"

    # --- Global pagination loop ---
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
                print(f"Skipping category: {cat_link_text}")
                continue
            print(f"Processing category: {cat_link_text}")
            cat_link.click()
            time.sleep(1)
            
            # --- Category-level pagination ---
            category_page_num = 1
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
                    if entry_index >= len(entries):
                        break
                    entry = entries[entry_index]
                    entry_text = entry.text
                    print(f"  Processing article: {entry_text}")
                    entry.click()
                    time.sleep(1)
                    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "fb")))
                    data = extract_from_fb_frame(driver)
                    print("    === EXTRACTED DATA ===")
                    print(data)
                    writer.writerow(data)
                    driver.switch_to.default_content()
                    driver.back()
                    time.sleep(1)
                # Try to click the next page button for this category
                category_page_num += 1
                next_cat_page_xpath = get_category_next_page_xpath(category_page_num)
                short_wait = WebDriverWait(driver, 2)  # 2 seconds for category paging
                try:
                    next_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, next_cat_page_xpath)))
                    print(f"    Clicking next page in category (page {category_page_num})...")
                    next_button.click()
                    time.sleep(2)
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                    print("    No more pages in this category.")
                    break

            driver.back()
            time.sleep(1)
        # --- Global pagination: try to click the next page link ---
        try:
            next_link = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_xpath)))
            print("Clicking next page...")
            next_link.click()
            time.sleep(2)
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
            print("No more pages or next page not clickable. Done.")
            break
finally:
    try:
        csv_file.close()
    except Exception:
        pass
    driver.quit()
    print("Scraping complete. CSV saved as output.csv.")
