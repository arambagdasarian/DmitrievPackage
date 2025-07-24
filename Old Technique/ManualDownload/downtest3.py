import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import csv
import time
from bs4 import BeautifulSoup

# Base configuration
START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/Users/aranbagdasarian/Documents/GitHub/ScrapeTestSNA/chromedriver"

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

def perform_login_and_search(driver, wait, from_date, to_date, download_dir):
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
    # Set date range
    from_date_input = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]"
    )))
    from_date_input.clear()
    from_date_input.send_keys(from_date)
    to_date_input = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[2]"
    )))
    to_date_input.clear()
    to_date_input.send_keys(to_date)
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]"
    )))
    driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
    search_btn.click()

def scrape_and_download(driver, wait, download_dir):
    # Wait for search results and click the new XPath link
    time.sleep(2)
    try:
        next_link = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[1]/table/tbody/tr/td[3]/a"
        )))
        next_link.click()
    except Exception as e:
        print(f"Could not click next link: {e}")
        return

    # Sort by date (using your new XPath)
    time.sleep(2)
    try:
        sort_date = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[2]/tbody/tr[4]/td/table/tbody/tr/td[2]/table/tbody/tr/td[8]/a"
        )))
        driver.execute_script("arguments[0].scrollIntoView(true);", sort_date)
        sort_date.click()
    except Exception as e:
        print(f"Could not click sort by date: {e}")
        return

    # Now handle the checkbox and download flow
    while True:
        # Select all checkboxes with name="doc"
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][name='doc']")
        for cb in checkboxes:
            try:
                cb.click()
            except Exception:
                pass

        # Find and click the "Open with MS Word" button
        try:
            word_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//td/input[@type='submit'][@value='Open with MS Word  (0.00 rub.)']"
            )))
            driver.execute_script("arguments[0].scrollIntoView(true);", word_btn)
            word_btn.click()
            time.sleep(2)  # Allow download to initiate
        except Exception as e:
            print(f"Could not click word button: {e}")

        # Find next page link and click if exists, else break
        try:
            next_page = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//a[contains(@href, 'ia5.aspx?lv=') and contains(text(), '>>')]"
            )))
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
            next_page.click()
            time.sleep(2)
        except (TimeoutException, NoSuchElementException):
            print("No more pages, ending.")
            break

# Main loop: from 2025 back to 2010
for year in range(2025, 2010, -1):
    from_date = f"01.01.{year-1}"
    to_date = f"01.01.{year}"
    download_dir = os.path.join(os.getcwd(), "scraped docs", str(year))
    os.makedirs(download_dir, exist_ok=True)

    # Configure Chrome for downloads for this year
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.default_content_settings.cookies": 2,
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)

    print(f"Processing {from_date} to {to_date}")
    try:
        perform_login_and_search(driver, wait, from_date, to_date, download_dir)
        scrape_and_download(driver, wait, download_dir)
    except Exception as e:
        print(f"Error processing {from_date} to {to_date}: {e}")
    finally:
        driver.quit()
