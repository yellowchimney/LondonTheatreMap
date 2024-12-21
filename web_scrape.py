import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import random
from typing import List, Dict, Any

def random_delay():
    delay = random.uniform(1, 3)
    time.sleep(delay)

def normalize_show_url(url: str) -> str:
    base_url = "https://www.londontheatre.co.uk"
    
    if "londontheatre.co.uk" in url:
        path = url.split("londontheatre.co.uk")[1]
    else:
        path = url
    
    path = path.strip("/").strip()
    parts = path.split("/")
    
    if len(parts) >= 2 and parts[0] == "show":
        show_parts = parts[1].split("-")
        show_id = show_parts[0]
        show_name = "-".join(show_parts[1:])
        
        if show_name.endswith("-tickets"):
            show_name = show_name[:-8]
        elif show_name.endswith("-"):
            show_name = show_name[:-1]
        
        if show_name:
            return f"{base_url}/show/{show_id}-{show_name}"
        return f"{base_url}/show/{show_id}"
    
    return f"{base_url}/{path}"

def get_show_urls() -> List[str]:
    show_urls = {}
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        
        url = "https://www.londontheatre.co.uk/whats-on"
        driver.get(url)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/show/']"))
        )
        
        last_count = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            try:
                load_more = driver.find_element(By.CSS_SELECTOR, "[class*='load-more'], [class*='loadMore'], .more-shows")
                if load_more.is_displayed():
                    load_more.click()
                    time.sleep(2)
            except:
                pass
            
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/show/']")
            current_count = len(links)
            
            if current_count == last_count:
                break
                
            last_count = current_count
        
        for link in links:
            href = link.get_attribute("href")
            if href and '/show/' in href:
                show_id = re.search(r'/show/(\d+)', href)
                if show_id and show_id.group(1) not in show_urls:
                    show_urls[show_id.group(1)] = normalize_show_url(href)
        
        return list(show_urls.values())
        
    finally:
        driver.quit()

def scrape_show_details(url: str) -> Dict[str, Any]:
    details = {
        'url': url,
        'name': None,
        'categories': [],
        'description': None,
        'start_date': None,
        'end_date': None,
        'starting_price': None,
        'venue_name': None,
        'venue_address': None
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        name_elem = soup.find(attrs={"data-test-id": "product-name"})
        if name_elem:
            details['name'] = name_elem.get_text(strip=True)

        desc_elem = soup.find('section', id='about-content')
        if desc_elem:
            details['description'] = ' '.join([p.get_text(strip=True) for p in desc_elem.find_all('p')])

        categories_section = soup.find(attrs={"data-test-id": "section-Categories"})
        if categories_section:
            category_links = categories_section.find_all('a')
            details['categories'] = [link.get_text(strip=True) for link in category_links]

        start_date_section = soup.find(attrs={"data-test-id": "section-Start date"})
        if start_date_section:
            start_date = start_date_section.find('p')
            if start_date:
                details['start_date'] = start_date.get_text(strip=True)

        end_date_section = soup.find(attrs={"data-test-id": "section-End date"})
        if end_date_section:
            end_date = end_date_section.find('p')
            if end_date:
                details['end_date'] = end_date.get_text(strip=True)

        price_elem = soup.find('div', class_='t-showtimes price')
        if price_elem:
            price_match = re.search(r'£\d+', price_elem.get_text())
            if price_match:
                details['starting_price'] = price_match.group()

        venue_name_elem = soup.find(attrs={"data-test-id": "venue-name"})
        if venue_name_elem:
            venue_link = venue_name_elem.find('a')
            if venue_link:
                details['venue_name'] = venue_link.get_text(strip=True)
            else:
                details['venue_name'] = venue_name_elem.get_text(strip=True)

        venue_address_elem = soup.find(attrs={"data-test-id": "venue-address"})
        if venue_address_elem:
            details['venue_address'] = venue_address_elem.get_text(strip=True)

        return details

    except Exception as e:
        return details

if __name__ == "__main__":
    show_urls = get_show_urls()
    all_details = []
    
    for idx, url in enumerate(show_urls, 1):
        random_delay()
        details = scrape_show_details(url)
        if details:
            all_details.append(details)
    
    df = pd.DataFrame(all_details)
    df.to_csv('london_theatre_shows_detailed.csv', index=False, encoding='utf-8')