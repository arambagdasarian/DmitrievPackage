from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
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

CHECKBOX_XPATHS = [
    "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[4]",
    # ... add other checkbox paths as needed ...
]
SEARCH_BUTTON_XPATH = (
    "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/"
    "table[1]/tbody/tr/td[3]/table[1]/tbody/tr[1]/td/table/tbody/tr/"
    "td[2]/table/tbody/tr/td[2]"
)

def extract_article_data_from_pre(pre_html):
    soup = BeautifulSoup(pre_html, "html.parser")
    text = soup.get_text("\n")
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    source = date = author = title = ''
    body_lines = []
    found_title = False

    for line in lines:
        if line.startswith('Источник:'):
            source = line.replace('Источник:', '').strip()
        elif line.startswith('Дата выпуска:'):
            date = line.replace('Дата выпуска:', '').strip()
        elif line.startswith('Автор:'):
            author_soup = BeautifulSoup(line, "html.parser")
            b = author_soup.find('b')
            author = b.get_text(strip=True) if b else author_soup.get_text(strip=True).replace('Автор:', '').strip()
        elif line.startswith('Заглавие:'):
            title = line.replace('Заглавие:', '').strip()
            found_title = True
        elif found_title:
            body_lines.append(line)

    body = '\n'.join(body_lines).strip()
    return {
        'source': source,
        'date': date,
        'author': author,
        'title': title,
        'body': body
    }

options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
service = ChromeService(executable_path=CHROMEDRIVER_PATH)

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

csv_file = open('output.csv', 'w', newline='', encoding='utf-8')
writer = csv.DictWriter(csv_file, fieldnames=['source','date','author','title','body'])
writer.writeheader()

try:
    driver.get(START_URL)
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "//input[@type='submit' and @value='Ich akzeptiere die Benutzungsbedingungen']"
    ))).click()
    id_field = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/"
        "tbody/tr[1]/td[2]/input"
    )))
    pw_field = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/"
        "tbody/tr[2]/td[2]/input"
    )))
    id_field.send_keys(USERNAME)
    pw_field.send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/"
        "tbody/tr[3]/td/input"
    ))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/form/table/tbody/tr[3]/td/input"
    ))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[3]/tbody/tr/td[2]/table/tbody/tr[2]/td/div[1]/a"
    ))).click()

    textarea = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/"
        "table[1]/tbody/tr/td[1]/textarea"
    )))
    textarea.clear()
    textarea.send_keys('"Кирилл Дмитриев"')

    for xp in CHECKBOX_XPATHS:
        try:
            chk = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView(true);", chk)
            chk.click()
        except Exception:
            pass

    date_input = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/"
        "span[1]/input[1]"
    )))
    date_input.clear()
    date_input.send_keys("01.01.2010")

    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, SEARCH_BUTTON_XPATH)))
    driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
    search_btn.click()

    time.sleep(1)
    categories = driver.find_elements(By.XPATH,
        "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
        "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
    )
    for cat in categories[:1]:  # process first category for now
        cat.click()
        time.sleep(1)
        entries = driver.find_elements(By.XPATH,
            "/html/body/table/tbody/tr[5]/td/table/tbody/tr/td/form/table[4]"
            "/tbody/tr/td/dt/a"
        )

        print("DEBUG PAGE SOURCE SNIPPET:")
        print(driver.page_source[:2000])  # Print the first 2000 characters for inspection

        for entry in entries:
            original = driver.current_window_handle
            entry.click()
            time.sleep(2)
            handles = driver.window_handles
            for h in handles:
                if h != original:
                    driver.switch_to.window(h)
                    break
            time.sleep(2)
            print("DEBUG URL:", driver.current_url)

            # Switch to iframe if present
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes")
            switched = False
            for idx, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    pres = driver.find_elements(By.TAG_NAME, 'pre')
                    if pres:
                        pre_html = pres[0].get_attribute('outerHTML')
                        print(f"Found <pre> in iframe {idx}")
                        data = extract_article_data_from_pre(pre_html)
                        print("DEBUG DATA:", data)
                        writer.writerow(data)
                        switched = True
                        driver.switch_to.default_content()
                        break
                    driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error switching to iframe {idx}: {e}")
                    driver.switch_to.default_content()
            if not switched:
                print("No <pre> tag found in any iframe or main page!")
                writer.writerow({'source':'', 'date':'', 'author':'', 'title':'', 'body':''})

            driver.close()
            driver.switch_to.window(original)
            time.sleep(1)
        driver.back()
        time.sleep(1)

finally:
    csv_file.close()
    driver.quit()
    print("Scraping complete. output.csv saved.")
