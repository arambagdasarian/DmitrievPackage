import os
import calendar
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
    "&license极长URL，已截断，请补全..."
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/Users/aranbagdasarian/Documents/GitHub/ScrapeTestSNA/chromedriver"

def generate_monthly_date_ranges(start_year, start_month, end_year, end_month):
    ranges = []
    current_year = start_year
    current_month = start_month
    while (current_year > end_year) or (current_year == end_year and current_month >= end_month):
        start_date = f"01.{current_month:02d}.{current_year}"
        last_day = calendar.monthrange(current_year, current_month)[1]
        end_date = f"{last_day:02d}.{current_month:02d}.{current_year}"
        ranges.append((start_date, end_date))
        if current_month == 1:
            current_month = 12
            current_year -= 1
        else:
            current_month -= 1
    return ranges

def perform_login_and_search(driver, wait, from_date, to_date):
    # Step 1: Load start URL and accept terms
    driver.get(START_URL)
    wait.until(EC.element_to_be_clickable((By.XPATH,
        "//input[@type='submit' and @value='Ich akzeptiere die Benutzungsbedingungen']"))).click()
    
    # Step 2: Fill credentials (using your original working XPaths)
    username_field = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[1]/td[2]/input")))
    username_field.send_keys(USERNAME)
    
    password_field = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[2]/td[2]/input")))
    password_field.send_keys(PASSWORD)
    
    # Step 3: Click login button
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/div[2]/div[3]/div/div/div/极长XPath，已截断，请补全..."
        "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[3]/td/input")))
    login_button.click()
    
    # Step 4: Click "Start Work" button
    start_work_button = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/form/table/tbody/tr[3]/td/input")))
    start_work_button.click()
    
    # Step 5: Navigate to search section
    search_section_link = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[3]/tbody/tr/td[2]/table/tbody/tr[2]/td/div[1]/a")))
    search_section_link.click()
    
    # Step 6: Fill search parameters
    ta = wait.until(EC.presence_of_element_located((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
    ta.clear()
    ta.send_keys('"Кирилл Дмитриев"')
    
    # Click all required checkboxes
    xpaths_to_click = [
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[4]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[8]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[12]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[15]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[16]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[17]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[1]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/极长XPath，已截断，请补全..."
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[11]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[10]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[3]",
    ]
    for xpath in xpaths_to_click:
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            el.click()
        except Exception as e:
            print(f"Could not click element at {xpath}: {e}")
    
    # Set date range
    from_date_input = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
    from_date_input.clear()
    from_date_input.send_keys(from_date)
    
    to_date_input = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[2]")))
    to_date_input.clear()
    to_date_input.send_keys(to_date)
    
    # Click search button
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
    search_btn.click()
    time.sleep(2)

def scrape_and_download(driver, wait, download_dir):
    # Go to Titles (results) section
    try:
        next_link = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[1]/table/tbody/tr/td[3]/a")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_link)
        next_link.click()
        time.sleep(2)
    except Exception as e:
        print(f"Could not click next link: {e}")
        return

    while True:
        # Scroll to the form containing checkboxes and download button
        try:
            form = wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", form)
            time.sleep(0.5)
        except Exception as e:
            print(f"Could not scroll to form: {e}")

        # Select all checkboxes
        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and @name='doc']")
        for cb in checkboxes:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
                if not cb.is_selected():
                    cb.click()
            except Exception as e:
                print(f"Could not click checkbox: {e}")

        # Click download button
        try:
            word_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//td/input[@type='submit' and @value='Open with MS Word  (0.00 rub.)']"
            )))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", word_btn)
            word_btn.click()
            time.sleep(2)
        except Exception as e:
            print(f"Could not click word button: {e}")

        # Pagination
        try:
            next_page = wait.until(EC.element_to_be_clickable((By.XPATH,
                "//a[contains(@href, 'ia5.aspx?lv=') and contains(text(), '>>')]"
            )))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page)
            next_page.click()
            time.sleep(2)
        except (TimeoutException, NoSuchElementException):
            print("No more pages, ending.")
            break

# Generate monthly date ranges: from July 2025 backwards to July 2010
monthly_ranges = generate_monthly_date_ranges(2025, 7, 2010, 7)

for from_date, to_date in monthly_ranges:
    year_month = f"{from_date[-4:]}-{from_date[3:5]}"
    download_dir = os.path.join(os.getcwd(), "scraped docs", year_month)
    os.makedirs(download_dir, exist_ok=True)

    options = Options()
    # Run in visible mode for debugging
    # options.add_argument("--headless")
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
    wait = WebDriverWait(driver, 20)

    print(f"Processing {from_date} to {to_date}")
    try:
        perform_login_and_search(driver, wait, from_date, to_date)
        scrape_and_download(driver, wait, download_dir)
    except Exception as e:
        print(f"Error processing {from_date} to {to_date}: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
