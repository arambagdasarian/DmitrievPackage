from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import csv
import time
import re

# --- Configuration ---
START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

# XPaths for checkbox selections
CHECKBOX_XPATHS = [
    "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[4]",
    # ... add other checkbox paths ...
]
# XPath for search button
SEARCH_BUTTON_XPATH = (
    "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/"
    "table[1]/tbody/tr/td[3]/table[1]/tbody/tr[1]/td/table/tbody/tr/"
    "td[2]/table/tbody/tr/td[2]"
)

# --- Setup WebDriver ---
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
service = ChromeService(executable_path=CHROMEDRIVER_PATH)

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

# --- CSV Setup ---
csv_file = open('output.csv', 'w', newline='', encoding='utf-8')
writer = csv.DictWriter(csv_file, fieldnames=['source','date','author','title','body'])
writer.writeheader()

try:
    # --- Login & Search Flow (unchanged) ---
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
    textarea.clear(); textarea.send_keys('"Кирилл Дмитриев"')
    for xp in CHECKBOX_XPATHS:
        try:
            chk = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].scrollIntoView(true);", chk)
            chk.click()
        except:
            pass
    date_input = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/"
        "span[1]/input[1]"
    )))
    date_input.clear(); date_input.send_keys("01.01.2010")
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, SEARCH_BUTTON_XPATH)))
    driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
    search_btn.click()

    # --- Scrape Categories & Entries with window-switching ---
    time.sleep(1)
    categories = driver.find_elements(By.XPATH,
        "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
        "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
    )
    for cat in categories[:1]:  # process first category for now
        cat.click(); time.sleep(1)
        entries = driver.find_elements(By.XPATH,
            "/html/body/table/tbody/tr[5]/td/table/tbody/tr/td/form/table[4]"
            "/tbody/tr/td/dt/a"
        )
        for entry in entries:
            original = driver.current_window_handle
            entry.click()
            time.sleep(1)
            # switch to new window if opened
            handles = driver.window_handles
            for h in handles:
                if h != original:
                    driver.switch_to.window(h)
                    break
            time.sleep(1)

            # now we can find <pre> blocks
            pres = driver.find_elements(By.XPATH, '/html/body/pre')
            print(f"Found {len(pres)} <pre> in article window")
            # combine all pre text
            full = "\n".join(p.get_attribute('textContent') for p in pres)

            # parse via regex
            pattern = (
                r"Источник:\s*(?P<source>.*?)\s*Дата выпуска:\s*(?P<date>.*?)"
                r"\s*Автор:\s*(?P<author>.*?)\s*Заглавие:\s*(?P<title>.*?)\s*(?P<body>[\s\S]+)"
            )
            m = re.search(pattern, full, flags=re.IGNORECASE)
            if m:
                writer.writerow(m.groupdict())
            else:
                print("Parse failed, content:\n", full[:200])

            # close article window and return
            driver.close()
            driver.switch_to.window(original)
            time.sleep(1)
        driver.back(); time.sleep(1)

finally:
    csv_file.close()
    driver.quit()
    print("Scraping complete. output.csv saved.")