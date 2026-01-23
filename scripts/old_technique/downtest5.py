import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/Users/aranbagdasarian/Documents/GitHub/ScrapeTestSNA/chromedriver"

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
        except Exception as e:
            print(f"Could not click element at {xpath}: {e}")
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
    time.sleep(2)

def scrape_and_download(driver, wait, download_dir):
    try:
        next_link = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[1]/table/tbody/tr/td[3]/a"
        )))
        driver.execute_script("arguments[0].scrollIntoView(true);", next_link)
        next_link.click()
        time.sleep(2)
    except Exception as e:
        print(f"Could not click next link: {e}")
        return

    while True:
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][name='doc']")
        for cb in checkboxes:
            try:
                cb.click()
            except Exception as e:
                print(f"Could not click checkbox: {e}")

        try:
            word_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//td/input[@type='submit'][@value='Open with MS Word  (0.00 rub.)']"
            )))
            driver.execute_script("arguments[0].scrollIntoView(true);", word_btn)
            word_btn.click()
            time.sleep(2)
        except Exception as e:
            print(f"Could not click word button: {e}")

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

# Main loop: 2025 first (01.01.2025 to 30.06.2025), then 2024 (01.01.2024 to 01.01.2025), etc. until 2010 (01.01.2010 to 01.01.2011)
year_ranges = [
    ("01.01.2025", "30.06.2025")
]
for year in range(2024, 2010, -1):
    year_ranges.append((f"01.01.{year}", f"01.01.{year+1}"))

for from_date, to_date in year_ranges:
    download_dir = os.path.join(os.getcwd(), "scraped docs", f"{from_date}-{to_date}")
    os.makedirs(download_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 15)

    print(f"Processing {from_date} to {to_date}")
    try:
        perform_login_and_search(driver, wait, from_date, to_date, download_dir)
        scrape_and_download(driver, wait, download_dir)
    except Exception as e:
        print(f"Error processing {from_date} to {to_date}: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
