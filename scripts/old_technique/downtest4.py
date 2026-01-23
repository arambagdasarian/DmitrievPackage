import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException

# Your original configuration
START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/Users/aranbagdasarian/Documents/GitHub/ScrapeTestSNA/chromedriver"

# Main loop: from 2025 back to 2010
for year in range(2025, 2010, -1):
    from_date = f"01.01.{year-1}"
    to_date = f"01.01.{year}"
    # Create folder for this year's downloads
    DOWNLOAD_DIR = os.path.join(os.getcwd(), "scraped docs", str(year))
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Configure Chrome for downloads for this year
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.default_content_settings.cookies": 2,
        "download.default_directory": DOWNLOAD_DIR,
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
        # Your original login and search flow
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
        # Use a reliable XPath for the search button
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]"
        )))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        search_btn.click()

        # Wait for search results and click the new XPath link
        time.sleep(2)
        next_link = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[1]/table/tbody/tr/td[3]/a"
        )))
        next_link.click()

        # Now handle the checkbox and download flow
        while True:
            # Select all checkboxes with name="doc"
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][name='doc']")
            for cb in checkboxes:
                try:
                    cb.click()
                except Exception as e:
                    print(f"Could not click checkbox: {e}")

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

    except Exception as e:
        print(f"Error processing {from_date} to {to_date}: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
