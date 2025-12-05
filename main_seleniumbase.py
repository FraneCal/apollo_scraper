# WORK IN PROGRESS

from seleniumbase import SB
from bs4 import BeautifulSoup
import time
import json

EMAIL = 'YOUR APOLLO EMAIL'
PASSWORD = 'YOUR APOLLO PASSWORD'
TARGET_URL = "YOUR APOLLO SAVED LIST"
LOGIN_URL = "https://app.apollo.io/#/login?locale=en"

def scrape_apollo(email, password, login_url, list_url, output_file="apollo_data.json"):
    all_data = []

    with SB(uc=True, headless=False) as sb:
        sb.open(login_url)
        # Login
        sb.type('input[name="email"]', email)
        sb.type('input[name="password"]', password)
        time.sleep(1)
        sb.click('form button[type="submit"]')
        sb.uc_gui_click_captcha()  # UC bypasses Turnstile

        # Wait for dashboard
        sb.wait_for_element_visible('.zp_gCXMt', timeout=30)
        sb.open(list_url)
        sb.wait_for_element_visible('div[data-testid="contact-name-cell"]', timeout=30)

        while True:
            time.sleep(2)  # small delay to let page fully render
            page_source = sb.get_page_source()
            soup = BeautifulSoup(page_source, "html.parser")

            # Extract data
            names = [n.get_text(strip=True) if n else "NA" for n in soup.find_all('span', class_='zp_pHNm5')]
            companies = [c.get_text(strip=True) if c else "NA" for i, c in enumerate(soup.find_all('span', class_='zp_xvo3G')) if i % 2 == 1]
            emails = [e.get_text(strip=True) if e else "NA" for i, e in enumerate(soup.find_all('span', class_='zp_xvo3G')) if i % 2 == 0]
            job_titles = [jt.get_text(strip=True) for i, jt in enumerate(soup.find_all('div', class_='zp_YGDgt')) if i % 2 == 0]
            locations = [loc.get_text(strip=True) for i, loc in enumerate(soup.find_all('div', class_='zp_YGDgt')) if i % 2 == 1]

            # Extract social media links per person
            social_blocks = soup.find_all('div', class_='zp_qR5tW')
            social_links_list = []
            for block in social_blocks:
                links = [a.get("href") for a in block.find_all('a') if a.get("href", "").startswith(("http://", "https://"))]
                social_links_list.append(links if links else ["NA"])

            # Combine all into dict per person
            for i in range(len(names)):
                person_data = {
                    "name": names[i] if i < len(names) else "NA",
                    "company": companies[i] if i < len(companies) else "NA",
                    "email": emails[i] if i < len(emails) else "NA",
                    "job_title": job_titles[i] if i < len(job_titles) else "NA",
                    "location": locations[i] if i < len(locations) else "NA",
                    "social_media": social_links_list[i] if i < len(social_links_list) else ["NA"]
                }
                all_data.append(person_data)

            # Try to go to next page
            try:
                btn = sb.find_element('button[aria-label="Next"]')

                # If the button is disabled exit the loop
                if btn.get_attribute("disabled") is not None:
                    break
                else:
                    sb.click('button[aria-label="Next"]')
                    sb.wait_for_element_visible('div[data-testid="contact-name-cell"]', timeout=30)

            except:
                break

    # Save all data to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"Scraping done. Data saved to {output_file}")

# Run scraper
scrape_apollo(EMAIL, PASSWORD, LOGIN_URL, TARGET_URL)
