from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from twocaptcha import TwoCaptcha
import time
import os

EMAIL = 'YOUR APOLLO EMAIL'
PASSWORD = 'YOUR APOLLO PASSWORD'
URL = "YOUR APOLLO SAVED LINK LIST"
LOGIN_URL = "https://app.apollo.io/#/login?locale=en"
TWO_CAPTCHA_API_KEY = "YOUR 2CAPTCHA API KEY"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0; IN) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 IN",
    "Mozilla/5.0 (Linux; Android 11; RMX2185) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-M315F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; M2101K7AI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 IN",
    "Mozilla/5.0 (Linux; Android 13; CPH2381) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; 2201116TI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
]

CHROME_DRIVER_ARGUMENTS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--start-maximized',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-gpu',
    '--disable-extensions',
    '--disable-application-cache',
    '--disable-dev-shm-usage',
    '--disable-popup-blocking',
    '--check-for-update-interval=31536000',
    '--disable-component-update',
    '--no-default-browser-check',
    "--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'"
]

STEALTH_JS = '''
(() => {
    delete Object.getPrototypeOf(navigator).webdriver;
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {0: {type: 'application/x-google-chrome-pdf', description: 'Portable Document Format'}},
            {0: {type: 'application/pdf', description: 'Portable Document Format'}}
        ]
    });
    Object.defineProperty(navigator, 'platform', {
        get: () => (/(Android|Linux)/.test(navigator.userAgent) ? 'Linux armv8l' : 'Win32')
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-IN','en','hi-IN']
    });
    Object.defineProperty(navigator, 'connection', {
        get: () => ({
            downlink: 10,
            effectiveType: '4g',
            rtt: 100,
            saveData: false,
            type: 'wifi'
        })
    });
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8
    });
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8
    });
    window.chrome = {
        app: { isInstalled: false },
        webstore: { onInstallStageChanged: {}, onDownloadProgress: {} },
        runtime: { }
    };
    Object.defineProperty(navigator, 'permissions', {
        get: () => ({
            query: (parameters) => (
                parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : Promise.resolve({ state: 'granted' })
            )
        })
    });
})();
'''

def captcha_solving():
    api_key = os.getenv('APIKEY_2CAPTCHA', TWO_CAPTCHA_API_KEY)

    solver = TwoCaptcha(api_key)

    try:
        result = solver.turnstile(
            sitekey='0x4AAAAAAA2OUu4yFDL9LSeZ',
            url=LOGIN_URL,
        )

    except Exception as e:
        print(e)

    else:
        print('solved: ' + str(result))

def login(email, password, url):
    options = Options()
    options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')

    for arg in CHROME_DRIVER_ARGUMENTS:
        options.add_argument(arg)

    driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": STEALTH_JS}
    )

    # Open the Login page
    driver.get(url)

    # Email field
    try:
        email_input_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'email')))
        ActionChains(driver).click(email_input_field).send_keys(email).perform()
    except TimeoutException:
        print("Email field was not clicked.")

    # Password input field
    try:
        password_wrapper = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']"))).find_element(By.XPATH,'//*[@id="provider-mounter"]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/div[3]/form/div/div[2]/div[2]/div[1]')
        ActionChains(driver).send_keys_to_element(password_wrapper, password).perform()
    except TimeoutException:
        print("Password field was not clicked.")

    # time.sleep(1)

    # Log in button
    try:
        log_in_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="provider-mounter"]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/div[3]/form/div/button')))
        ActionChains(driver).click(log_in_button).perform()
    except TimeoutException:
        print("No button found.")

    try:
        captcha_solving()
    except Exception as e:
        print(f"captcha_solving() failed or not needed: {e}")

    return driver

def site_navigation(driver, url):
    # Wait until the homepage appears
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'zp_gCXMt')))

    # Go to the list link
    driver.get(url)

    # Wait until the list shows
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='contact-name-cell']")))

    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        next_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main-container-column-2"]/div[2]/div[2]/div[2]/div/div[2]/div/div[2]/button[2]')))
        next_page.click()
    except TimeoutException:
        print("Email field was not clicked.")

    time.sleep(5)

    page_source = driver.page_source

    driver.quit()

    soup = BeautifulSoup(page_source, "html.parser")

    names = [name.getText() if name is not None else "NA" for name in (soup.find_all('span', class_='zp_pHNm5'))]
    companies = [company.getText() if company is not None else "NA" for i, company in enumerate(soup.find_all('span', class_='zp_xvo3G')) if i % 2 == 1]
    emails = [email.getText() if email is not None else "NA" for i, email in enumerate(soup.find_all('span', class_='zp_xvo3G')) if i % 2 == 0]
    job_titles = [job_title.getText() for i, job_title in enumerate(soup.find_all('div', class_='zp_YGDgt')) if i % 2 == 0]
    locations = [location.getText() for i, location in enumerate(soup.find_all('div', class_='zp_YGDgt')) if i % 2 == 1]
    social_media_links = [social_media_link.get("href") if social_media_link is not None else "NA" for social_media_link in (soup.find_all('div', class_='zp_qR5tW').find_all('a'))]

    for s in social_media_links:
        print(s)

    print(len(social_media_links))

driver = login(EMAIL, PASSWORD, LOGIN_URL)
site_navigation(driver, URL)
