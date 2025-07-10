#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import time

START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "../chromedriver"

def test_category_pagination():
    """Test how many category pages exist and verify pagination is working"""
    
    options = Options()
    options.add_argument("--headless")
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("=== TESTING CATEGORY PAGINATION ===")
        
        # Login and search
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
        
        # Search
        ta = wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
        ta.clear()
        ta.send_keys('"Кирилл Дмитриев"')
        
        dp = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
        dp.clear()
        dp.send_keys("01.01.2010")
        
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        search_btn.click()
        
        time.sleep(2)
        
        # Test category pagination
        cat_xpath = (
            "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
            "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
        )
        next_page_xpath = "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[3]/td/table/tbody/tr/td[2]/a[2]"
        
        category_page_count = 0
        total_categories = 0
        
        while True:
            category_page_count += 1
            
            # Count categories on this page
            categories = driver.find_elements(By.XPATH, cat_xpath)
            page_categories = len(categories)
            total_categories += page_categories
            
            print(f"Category page {category_page_count}: {page_categories} categories")
            
            # Show first few categories on this page
            for i, cat in enumerate(categories[:3]):
                cat_text = cat.text.strip()
                print(f"  - {cat_text}")
            
            if page_categories > 3:
                print(f"  ... and {page_categories - 3} more")
            
            # Try to go to next category page
            try:
                next_link = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_xpath)))
                print(f"  --> Next page button found, clicking...")
                next_link.click()
                time.sleep(2)
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                print(f"  --> No more category pages. Reason: {type(e).__name__}")
                break
        
        print(f"\n=== SUMMARY ===")
        print(f"Total category pages found: {category_page_count}")
        print(f"Total categories across all pages: {total_categories}")
        
        # Test if going beyond current limit finds more
        print(f"\n=== EXTENDED DATE RANGE TEST ===")
        
        # Go back to search and try with 1990 date
        driver.back()
        driver.back()
        driver.back()
        
        ta = wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
        ta.clear()
        ta.send_keys('"Кирилл Дмитриев"')
        
        dp = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
        dp.clear()
        dp.send_keys("01.01.1990")  # Extended date range
        
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        search_btn.click()
        
        time.sleep(2)
        
        # Count with extended date
        extended_categories = driver.find_elements(By.XPATH, cat_xpath)
        print(f"Categories with 1990+ date range: {len(extended_categories)}")
        
        return {
            "total_category_pages": category_page_count,
            "total_categories_2010": total_categories,
            "total_categories_1990": len(extended_categories)
        }
        
    finally:
        driver.quit()

if __name__ == "__main__":
    results = test_category_pagination()
    print(f"\n=== FINAL DIAGNOSIS ===")
    print(f"Your script should process {results['total_category_pages']} category pages")
    print(f"Total categories available (2010+): {results['total_categories_2010']}")
    print(f"Total categories available (1990+): {results['total_categories_1990']}")
    
    if results['total_category_pages'] > 1:
        print(f"\n❌ ISSUE CONFIRMED: Multiple category pages exist!")
        print(f"If your script only found ~80 categories, it's missing {results['total_categories_2010'] - 80} categories")
    else:
        print(f"\n✅ Category pagination is not the issue") 