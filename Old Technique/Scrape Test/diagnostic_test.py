#!/usr/bin/env python3
import re
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

def test_search_variations():
    options = Options()
    options.add_argument("--headless")
    service = ChromeService(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    
    # Test different search terms and date ranges
    test_scenarios = [
        {"term": '"Кирилл Дмитриев"', "start_date": "01.01.2010", "description": "Current method"},
        {"term": '"Кирилл Дмитриев"', "start_date": "01.01.1990", "description": "Extended date range"},
        {"term": 'Кирилл Дмитриев', "start_date": "01.01.1990", "description": "No quotes, extended date"},
        {"term": '"К. Дмитриев"', "start_date": "01.01.1990", "description": "Initials variant"},
        {"term": '"Kirill Dmitriev"', "start_date": "01.01.1990", "description": "English variant"},
    ]
    
    results = []
    
    for scenario in test_scenarios:
        try:
            print(f"\n=== Testing: {scenario['description']} ===")
            
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
            
            # Search setup
            ta = wait.until(EC.presence_of_element_located((By.XPATH,
                "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea")))
            ta.clear()
            ta.send_keys(scenario['term'])
            
            # Set date
            dp = wait.until(EC.element_to_be_clickable((By.XPATH,
                "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]")))
            dp.clear()
            dp.send_keys(scenario['start_date'])
            
            # Execute search
            search_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
                "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]//tr/td[2]")))
            driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
            search_btn.click()
            
            time.sleep(2)
            
            # Count total results
            try:
                # Look for results summary or category count
                cat_xpath = (
                    "/html/body/table/tbody/tr[5]/td/table[2]/tbody/tr[2]/td/table/tbody/"
                    "tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr[position()>1]/td[1]/a"
                )
                categories = driver.find_elements(By.XPATH, cat_xpath)
                
                total_categories = len(categories)
                category_info = []
                
                for i, cat in enumerate(categories[:5]):  # Check first 5 categories
                    cat_text = cat.text.strip()
                    # Try to find result count for each category
                    count_element = cat.find_element(By.XPATH, "./following-sibling::td")
                    count_text = count_element.text if count_element else "Unknown"
                    category_info.append(f"{cat_text}: {count_text}")
                
                result = {
                    "scenario": scenario['description'],
                    "term": scenario['term'],
                    "start_date": scenario['start_date'],
                    "total_categories": total_categories,
                    "sample_categories": category_info
                }
                results.append(result)
                
                print(f"Found {total_categories} categories")
                for cat_info in category_info:
                    print(f"  - {cat_info}")
                    
            except Exception as e:
                print(f"Error counting results: {e}")
                results.append({
                    "scenario": scenario['description'],
                    "error": str(e)
                })
            
        except Exception as e:
            print(f"Failed: {e}")
            results.append({
                "scenario": scenario['description'],
                "error": str(e)
            })
    
    driver.quit()
    return results

if __name__ == "__main__":
    print("=== DIAGNOSTIC TEST FOR SEARCH LIMITATIONS ===")
    results = test_search_variations()
    
    print("\n=== SUMMARY ===")
    for result in results:
        if "error" not in result:
            print(f"{result['scenario']}: {result['total_categories']} categories found")
        else:
            print(f"{result['scenario']}: ERROR - {result['error']}") 