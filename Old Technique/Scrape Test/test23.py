import re
import csv
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (TimeoutException, NoSuchElementException, 
                                       ElementClickInterceptedException, StaleElementReferenceException)
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "/Users/aranbagdasarian/Documents/GitHub/ScrapeTestSNA/chromedriver"


def plausible_author(val):
    if not val: 
        return False
    if len(val) > 40: 
        return False
    badwords = ["Источник", "Дата", "Заглавие", "Номер выпуска", "Best.ru", "http", "www.", "Премия"]
    if any(bad in val for bad in badwords): 
        return False
    if any(char.isdigit() for char in val): 
        return False
    return True

def plausible_source(val):
    if not val: 
        return False
    badwords = ["Дата", "Заглавие", "Автор", "Номер выпуска", "Best.ru", "Премия"]
    if any(bad in val for bad in badwords): 
        return False
    return True

def plausible_title(val):
    if not val: 
        return False
    badwords = ["Источник", "Дата", "Автор", "Номер выпуска", "Best.ru", "Премия"]
    if any(bad in val for bad in badwords): 
        return False
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
    data = {'source': '', 'date': '', 'author': '', 'title': '', 'body': ''}

    # Extraction logic remains the same as your original
    # ... [YOUR EXISTING EXTRACTION LOGIC] ...
    
    return data

# Initialize driver
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
    "profile.default_content_settings.cookies": 2
}
options.add_experimental_option("prefs", prefs)
service = ChromeService(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

try:
    # Login sequence
    logger.info("Navigating to start URL")
    driver.get(START_URL)
    
    # Step-by-step login with robust waiting
    login_steps = [
        ("//input[@type='submit' and @value='Ich akzeptiere die Benutzungsbedingungen']", "click"),
        ("/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[1]/td[2]/input", "send_keys", USERNAME),
        ("/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[2]/td[2]/input", "send_keys", PASSWORD),
        ("/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[3]/td/input", "click"),
        ("/html/body/form/table/tbody/tr[3]/td/input", "click"),
        ("/html/body/table[3]/tbody/tr/td[2]/table/tbody/tr[2]/td/div[1]/a", "click")
    ]
    
    for step in login_steps:
        try:
            element = wait.until(EC.element_to_be_clickable((By.XPATH, step[0])))
            if step[1] == "click":
                element.click()
            elif step[1] == "send_keys":
                element.clear()
                element.send_keys(step[2])
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error at login step: {step[0]} - {str(e)}")
            raise
    
    # Search configuration
    logger.info("Configuring search parameters")
    ta = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
    ta.clear()
    ta.send_keys('"Кирилл Дмитриев"')
    
    checkboxes = [
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[4]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[8]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[12]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[15]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[16]",
        "/html/body/table[1]/tbody/tr[3]/td/article/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[1]/input[17]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[1]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[11]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[10]",
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[2]/tbody/tr[2]/td[2]/input[3]",
    ]
    
    for xpath in checkboxes:
        try:
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            el.click()
            time.sleep(0.2)
        except Exception as e:
            logger.warning(f"Couldn't click checkbox at {xpath}: {str(e)}")
    
    dp = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
    dp.clear()
    dp.send_keys("01.01.2010")
    
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
    search_btn.click()
    time.sleep(2)
    
    # CSV setup
    csv_file = open('output.csv', 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(csv_file, fieldnames=['source', 'date', 'author', 'title', 'body', 'url'])
    writer.writeheader()
    
    # Category processing
    logger.info("Starting category processing")
    cat_xpath = "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
    
    # Pagination handling
    page_count = 0
    while True:
        page_count += 1
        logger.info(f"Processing category menu page {page_count}")
        
        # Get current categories
        categories = wait.until(EC.presence_of_all_elements_located((By.XPATH, cat_xpath)))
        logger.info(f"Found {len(categories)} categories on page {page_count}")
        
        for idx in range(len(categories)):
            # Re-fetch to avoid staleness
            categories = wait.until(EC.presence_of_all_elements_located((By.XPATH, cat_xpath)))
            if idx >= len(categories):
                break
                
            cat = categories[idx]
            cat_text = cat.text.strip()
            
            if "pdf" in cat_text.lower() or "архив" in cat_text.lower():
                logger.info(f"Skipping PDF/archive category: {cat_text}")
                continue
                
            logger.info(f"Clicking category: {cat_text}")
            try:
                cat.click()
                time.sleep(1.5)  # Allow page to load
            except StaleElementReferenceException:
                logger.warning("Stale element when clicking category, retrying...")
                categories = wait.until(EC.presence_of_all_elements_located((By.XPATH, cat_xpath)))
                categories[idx].click()
                time.sleep(1.5)
                
            # Article processing
            article_page = 1
            while True:
                logger.info(f"Processing article page {article_page}")
                
                # Process articles
                entries_xpath = "/html/body/table/tbody/tr[5]/td/table/tbody/tr/td/form/table[4]/tbody/tr/td/dt/a"
                entries = wait.until(EC.presence_of_all_elements_located((By.XPATH, entries_xpath)))
                
                for entry_idx in range(len(entries)):
                    # Re-fetch entries to avoid staleness
                    entries = wait.until(EC.presence_of_all_elements_located((By.XPATH, entries_xpath)))
                    if entry_idx >= len(entries):
                        break
                        
                    entry = entries[entry_idx]
                    entry_text = entry.text
                    article_url = entry.get_attribute("href")
                    
                    try:
                        entry.click()
                        time.sleep(0.5)
                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "fb")))
                    except (TimeoutException, StaleElementReferenceException):
                        logger.warning("Error switching to frame, retrying...")
                        driver.switch_to.default_content()
                        driver.back()
                        time.sleep(1)
                        continue
                        
                    data = extract_from_fb_frame(driver, fallback_title=entry_text)
                    data['url'] = article_url
                    writer.writerow(data)
                    
                    driver.switch_to.default_content()
                    driver.back()
                    time.sleep(1)
                
                # Article pagination - find next button using text
                next_found = False
                pagination_cells = driver.find_elements(By.XPATH, "//td[contains(@class, 'txt')]")
                
                for cell in pagination_cells:
                    links = cell.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        if link.text.strip() == ">>":
                            logger.info("Found next article page button")
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                                link.click()
                                time.sleep(1.5)
                                next_found = True
                                article_page += 1
                                break
                            except Exception as e:
                                logger.error(f"Error clicking next article button: {str(e)}")
                    if next_found:
                        break
                
                if not next_found:
                    logger.info("No more article pages in this category")
                    break
                    
            # Return to category menu
            driver.back()
            time.sleep(1.5)
        
        # Category menu pagination - find next button using text
        next_found = False
        pagination_tables = driver.find_elements(By.XPATH, "//table[contains(@class, 'maintxt')]")
        
        for table in pagination_tables:
            links = table.find_elements(By.TAG_NAME, "a")
            for link in links:
                if link.text.strip() == ">>":
                    logger.info("Found next category page button")
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", link)
                        link.click()
                        time.sleep(2.5)  # Allow full page load
                        next_found = True
                        break
                    except Exception as e:
                        logger.error(f"Error clicking next category button: {str(e)}")
            if next_found:
                break
                
        if not next_found:
            logger.info("No more category pages to process")
            break
            
finally:
    logger.info("Closing resources")
    try:
        csv_file.close()
    except:
        pass
    driver.quit()
    logger.info("Scraping completed")
