import os
import random
import time
import pandas as pd
import re
from itertools import repeat, zip_longest
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_webdriver(user_agents):
    service = Service()
    options = Options()
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    # options.add_argument("--headless")  # Uncomment this line for headless mode
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

def login(driver, email, password, url):
    driver.get(url)
    email_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'email')))
    email_input.send_keys(email)

    password_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'password')))
    password_input.send_keys(password)

    log_in_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="provider-mounter"]/div/div[2]/div/div[1]/div/div[2]/div/div[2]/div/form/div[4]/button')))
    log_in_button.click()

    time.sleep(5)

def get_text_or_default(element, default=''):
    return element.text.strip() if element else default

def scrape_data(driver, num_pages_to_scrape, excel_file_path):
    page_num = 0

    print("Starting to scrape! :)")

    while page_num < num_pages_to_scrape:
        page_num += 1
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Initialize the data dictionary for this page
        page_data = {
            'Business Name': [],
            'Website': [],
            'Niche': [],
            'Country': [],
            'First Name': [],
            'Last Name': [],
            'Job Title': [],
            'Phone number': [],
            'Personal email': [],
            'Personal LinkedIn': [],
            'Company LinkedIn': [],
        }

        # Extracting names
        names = [name.text.split(maxsplit=1) for name in soup.find_all('div', class_='zp_xVJ20') if name.find('a')]
        first_name, last_name = zip_longest(*names, fillvalue='')

        # Extracting websites
        websites = [a.get('href') for a in soup.find_all('a', class_='zp-link zp_OotKe')
                    if a.get('href') and not a.get('href').startswith('#') and not any(social in a.get('href') for social in ["facebook", "linkedin", "twitter", "apollo", "Facebook"])]
        company_names = [get_text_or_default(name.find('a'), "Company not found") for name in soup.find_all('div', class_='zp_J1j17')]
        websites.extend(["Website not specified"] * (len(company_names) - len(websites)))
        
        # Extracting company LinkedIn links
        company_linkedin_list = [a.get('href') for a in soup.find_all('a', class_='zp-link zp_OotKe')
                                 if a.get('href') and "linkedin" in a.get('href') and "company" in a.get('href')]
        company_linkedin_list.extend(["LinkedIn page not specified"] * (len(company_names) - len(company_linkedin_list)))
        
        # Extracting personal LinkedIn links
        personal_linkedin_list = [a.get('href') for a in soup.find_all('a', class_='zp-link zp_OotKe')
                                  if a.get('href') and "linkedin" in a.get('href') and "company" not in a.get('href')]

        # Extracting industries
        industries = soup.find_all('span', class_='zp_PHqgZ zp_TNdhR')
        industries = soup.find_all('span', class_='zp_PHqgZ zp_TNdhR')[:25]  # Limit to 25 elements
        industries_list = [industry.text.strip() for industry in industries if industry is not None]

        # Extracting locations
        locations = soup.find_all('span', class_='zp_Y6y8d')
        locations_list = [location.text.strip() for location in locations if location is not None and (location.text.strip().endswith(", Australia") or location.text.strip() == "Australia")]

        # Extracting job titles
        titles = [get_text_or_default(title) for title in soup.find_all('span', class_='zp_Y6y8d')[::3]]

        # Extracting company names
        company_names = [get_text_or_default(name.find('a'), "Company not found") for name in soup.find_all('div', class_='zp_J1j17')]

        # Extracting phone numbers
        phone_numbers = soup.find_all('span', class_='zp_lm1kV')
        phone_numbers_clean = [phone.find('a') for phone in phone_numbers]
        phone_numbers = [phone.text.strip() for phone in phone_numbers_clean if phone is not None]

        # Extracting emails
        emails = [get_text_or_default(email.find('a', class_='zp-link zp_OotKe zp_Iu6Pf')) for email in soup.find_all('div', class_='zp_jcL6a')]

        page_data['Business Name'].extend(company_names)
        page_data['Website'].extend(websites)
        page_data['Niche'].extend(industries_list)
        page_data['Country'].extend(locations_list)
        page_data['First Name'].extend(first_name)
        page_data['Last Name'].extend(last_name)
        page_data['Job Title'].extend(titles)
        page_data['Phone number'].extend(phone_numbers)
        page_data['Personal email'].extend(emails)
        page_data['Personal LinkedIn'].extend(personal_linkedin_list)
        page_data['Company LinkedIn'].extend(company_linkedin_list)

        # PRINT OUT WHAT IS THE LENGTH OF EACH COLUMN TO MAKE SURE THEY ARE THE SAME
        for column, data_list in page_data.items():
            print(f"{column}: {len(data_list)}")

        # Save the data for this page
        df = pd.DataFrame(page_data)
        save_to_excel(df, excel_file_path)

        # Reset page_data to avoid carrying over data to the next page
        page_data = {
            'Business Name': [],
            'Website': [],
            'Niche': [],
            'Country': [],
            'First Name': [],
            'Last Name': [],
            'Job Title': [],
            'Phone number': [],
            'Personal email': [],
            'Personal LinkedIn': [],
            'Company LinkedIn': [],
        }

        if page_num < num_pages_to_scrape:
            try:
                print(f'Scraping page {page_num}/{num_pages_to_scrape}.')
                next_page_button = driver.find_element(By.XPATH, '//*[@id="main-app"]/div[2]/div/div/div[2]/div[2]/div/div[2]/div/div/div/div/div/div/div[2]/div/div[4]/div/div/div/div/div[3]/div/div[2]/button[2]')
                next_page_button.click()
                time.sleep(3)
            except NoSuchElementException:
                print("No next page button found.")
                break

def save_to_excel(df, excel_file_path):
    if os.path.isfile(excel_file_path):
        existing_df = pd.read_excel(excel_file_path)
        df_no_duplicates = pd.concat([existing_df, df]).drop_duplicates(keep='last')
        df_no_duplicates.to_excel(excel_file_path, index=False)
    else:
        df.to_excel(excel_file_path, index=False)
    print(f"Data saved to {excel_file_path}")

def remove_duplicates(input_file, output_file):
    df = pd.read_excel(input_file)
    if df.duplicated().any():
        df_no_duplicates = df.drop_duplicates()
        df_no_duplicates.to_excel(output_file, index=False)
        print(f"Duplicate rows removed and saved to {output_file}")
    else:
        df.to_excel(output_file, index=False)
        print("No duplicate rows found. Data remains unchanged.")

if __name__ == "__main__":
    URL = "YOUR APOLLO SAVED LIST LINK"
    user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"]
    
    email = 'YOUR APOLLO EMAIL'
    password = 'YOUR APOLLO PASSWORD'

    driver = setup_webdriver(user_agents)
    login(driver, email, password, URL)

    num_pages_to_scrape = 2
    excel_file_path = 'complete_data_2.xlsx'
    scrape_data(driver, num_pages_to_scrape, excel_file_path)

    driver.quit()

    output_file_path = "output_file_2.xlsx"
    remove_duplicates(excel_file_path, output_file_path)
