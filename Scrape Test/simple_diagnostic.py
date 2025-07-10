#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time

START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"
CHROMEDRIVER_PATH = "../chromedriver"

def analyze_current_search():
    """Analyze what the current search method finds"""
    
    options = Options()
    options.add_argument("--headless")
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("=== ANALYZING CURRENT SEARCH METHOD ===")
        
        # Login process
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
        
        # Search with current method
        ta = wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
        ta.clear()
        ta.send_keys('"Кирилл Дмитриев"')
        
        # Set date to 2010 (current method)
        dp = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
        dp.clear()
        dp.send_keys("01.01.2010")
        
        # Execute search
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        search_btn.click()
        
        time.sleep(2)
        
        # Analyze results
        cat_xpath = (
            "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
            "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
        )
        categories = driver.find_elements(By.XPATH, cat_xpath)
        
        print(f"Found {len(categories)} categories")
        
        # Analyze each category
        category_data = []
        for i, cat in enumerate(categories):
            cat_text = cat.text.strip()
            # Try to find count in next column
            try:
                count_element = cat.find_element(By.XPATH, "./following-sibling::td")
                count_text = count_element.text.strip()
            except:
                count_text = "Unknown"
            
            category_data.append({
                "name": cat_text,
                "count": count_text
            })
            
            if i < 10:  # Show first 10
                print(f"  {i+1}. {cat_text}: {count_text}")
        
        # Look for total count or pagination info
        try:
            # Look for total results indicator
            page_text = driver.page_source
            if "Treffer" in page_text:
                import re
                treffer_match = re.search(r'(\d+)\s*Treffer', page_text)
                if treffer_match:
                    total_hits = treffer_match.group(1)
                    print(f"\nTotal search hits found: {total_hits}")
        except:
            pass
        
        # Check pagination at category level
        try:
            next_page_xpath = "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[3]/td/table/tbody/tr/td[2]/a[2]"
            next_page = driver.find_element(By.XPATH, next_page_xpath)
            if next_page:
                print("Category pagination available - more categories exist")
        except:
            print("No category pagination found")
        
        return category_data
        
    finally:
        driver.quit()

def test_date_range_impact():
    """Test if changing date range affects results"""
    
    options = Options()
    options.add_argument("--headless")
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("\n=== TESTING DATE RANGE IMPACT ===")
        
        # Login process (same as above)
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
        
        # Search with same term but different date
        ta = wait.until(EC.presence_of_element_located((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
        ta.clear()
        ta.send_keys('"Кирилл Дмитриев"')
        
        # Set date to 1990 (extended range)
        dp = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
        dp.clear()
        dp.send_keys("01.01.1990")
        
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        search_btn.click()
        
        time.sleep(2)
        
        # Count categories with extended date range
        cat_xpath = (
            "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
            "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
        )
        categories_extended = driver.find_elements(By.XPATH, cat_xpath)
        
        print(f"With date from 1990: {len(categories_extended)} categories")
        
        # Look for total count
        try:
            page_text = driver.page_source
            if "Treffer" in page_text:
                import re
                treffer_match = re.search(r'(\d+)\s*Treffer', page_text)
                if treffer_match:
                    total_hits_extended = treffer_match.group(1)
                    print(f"Total search hits with extended date: {total_hits_extended}")
        except:
            pass
            
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_current_search()
    test_date_range_impact() 