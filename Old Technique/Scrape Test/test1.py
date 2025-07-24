from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time

# --- Configuration ---
START_URL = (
    "https://dbis.uni-regensburg.de/warpto?ubr_id=SBBPK&resource_id=9032"
    "&license_type=3&license_form=31&access_type=1&access_form=&access_id=32045"
)
USERNAME = "X240451"
PASSWORD = "AZoeypewc1#"

# Path to your chromedriver executable
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

# --- Setup WebDriver ---
options = Options()
# options.add_argument("--headless")  # enable if needed
options.add_argument("--disable-gpu")
service = ChromeService(executable_path=CHROMEDRIVER_PATH)

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

try:
    # 1. Navigate to the start URL
    driver.get(START_URL)

    # 2. Accept terms of use by clicking the submit button
    accept_button = wait.until(
        EC.element_to_be_clickable((By.XPATH,
            "//input[@type='submit' and @value='Ich akzeptiere die Benutzungsbedingungen']"
        ))
    )
    accept_button.click()

    # 3. Fill in ID and password using provided XPaths
    id_field = wait.until(
        EC.presence_of_element_located((By.XPATH,
            "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[1]/td[2]/input"
        ))
    )
    pw_field = wait.until(
        EC.presence_of_element_located((By.XPATH,
            "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[2]/td[2]/input"
        ))
    )
    id_field.send_keys(USERNAME)
    pw_field.send_keys(PASSWORD)

    # 4. Click on the login button
    login_button = wait.until(
        EC.element_to_be_clickable((By.XPATH,
            "/html/body/div[2]/div[3]/div/div/div/div/div[2]/div/div[2]/div/div/form/table/tbody/tr[3]/td/input"
        ))
    )
    login_button.click()

    # 5. Click on "Enter (no registration)"
    enter_no_reg = wait.until(
        EC.element_to_be_clickable((By.XPATH,
            "/html/body/form/table/tbody/tr[3]/td/input"
        ))
    )
    enter_no_reg.click()

    # 6. Click on "artefact" using provided XPath
    artefact_link = wait.until(
        EC.element_to_be_clickable((By.XPATH,
            "/html/body/table[3]/tbody/tr/td[2]/table/tbody/tr[2]/td/div[1]/a"
        ))
    )
    artefact_link.click()

# 7. Write "Кирилл Дмитриев" into the textarea using the given XPath
    textarea = wait.until(
    EC.presence_of_element_located((By.XPATH,
        "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[1]/textarea"
    ))
)
    textarea.clear()  # Optional: clear any pre-filled text
    textarea.send_keys('"Кирилл Дмитриев"')
    print('Text written to textarea successfully.')


    print("Reached the query menu (artefact) successfully.")

    # 8. Click on the specified boxes/links by their XPaths
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
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)  # Scroll into view if needed
            element.click()
            print(f"Clicked element: {xpath}")
            time.sleep(0.2)  # Optional: slight pause between clicks for reliability
        except Exception as e:
            print(f"Could not click element {xpath}: {e}")

    # 9. Clear and fill the date input box
    date_input_xpath = "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/span[1]/input[1]"
    date_input = wait.until(
        EC.element_to_be_clickable((By.XPATH, date_input_xpath))
    )
    date_input.clear()
    date_input.send_keys("01.01.2010")
    print('Date input set to 01.01.2010')


        # 10. Click on the "search" button using the given XPath
    search_button_xpath = "/html/body/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/form/table[1]/tbody/tr/td[3]/table[1]/tbody/tr[1]/td/table/tbody/tr/td[2]/table/tbody/tr/td[2]"
    search_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, search_button_xpath))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search_button)  # Ensure it's in view
    search_button.click()
    print("Search button clicked.")


finally:
    # Pause briefly for inspection
    time.sleep(2)
    driver.quit()

