import requests
from bs4 import BeautifulSoup
import re
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# Common Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def clean_phone(phone):
    """Clean phone number string."""
    if not phone:
        return None
    # Remove all non-digit characters
    clean = re.sub(r'\D', '', str(phone))
    return clean

def is_valid_mobile_string(phone_str):
    """
    Validates if the phone string contains a valid Indian mobile number.
    Returns the mobile number if valid, else None.
    """
    clean = clean_phone(phone_str)
    if not clean:
        return None
        
    # Handle +91 or 0 prefix
    if clean.startswith('91') and len(clean) > 10:
        clean = clean[2:]
    elif clean.startswith('0') and len(clean) > 10:
        clean = clean[1:]
        
    # Strictly 10 digits
    if len(clean) != 10:
        return None
        
    # Starts with 6, 7, 8, 9
    if clean[0] not in ['6', '7', '8', '9']:
        return None
        
    return clean

def fetch_url(url, use_playwright=False):
    """
    Fetches URL content. 
    Retries with Playwright if standard request fails or is blocked.
    """
    if not use_playwright:
        try:
            time.sleep(random.uniform(1, 3))
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                # Basic block checks
                lower_text = response.text.lower()
                if "captcha" in lower_text or "access denied" in lower_text or "robot" in lower_text:
                    pass # Fall through to Playwright
                else:
                    return response.text
        except Exception as e:
            pass # Fall through to Playwright

    # Playwright Fallback
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=HEADERS['User-Agent'])
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Check for "Reveal Number" buttons and click them if possible
                # Specific selectors for different sites
                # Justdial: .callbutton, .contact-number
                # IndiaMART: .pnm
                # This is a best-effort generic clicker
                
                # Wait a bit for JS to load
                page.wait_for_timeout(2000)
                
                content = page.content()
            except Exception as e:
                content = None
                
            browser.close()
            return content
    except Exception as e:
        return None

def scrape_justdial(category, pincode):
    """Scrape Justdial for a category and pincode."""
    base_url = f"https://www.justdial.com/India/Search"
    # Justdial search format: "Category in Pincode" usually works well
    query = f"{category} in {pincode}"
    url = f"{base_url}?q={query}"
    
    html = fetch_url(url)
    results = []
    
    if not html:
        return results
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Justdial selectors (these change, trying generic classes)
    # Look for result cards
    cards = soup.select('.resultbox_info') or soup.find_all('div', class_=lambda c: c and 'store-details' in c) or soup.select('.lxT77') # 2024 classes
    
    if not cards:
        # Try generic article or list items
        cards = soup.find_all('div', class_=re.compile(r'result|card|store'))
    
    for card in cards:
        try:
            name_tag = card.find('h2') or card.find('div', class_='store-name') or card.find('span', class_='lng_cont_name')
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            
            # Phone extraction is tricky on JD. Sometimes in icons, sometimes text.
            # We look for typical phone patterns in the whole card text first
            card_text = card.get_text(" ", strip=True)
            phones = re.findall(r'\b[6-9]\d{9}\b', card_text)
            
            # Filter valid mobiles
            valid_mobile = None
            for p in phones:
                if is_valid_mobile_string(p):
                    valid_mobile = is_valid_mobile_string(p)
                    break
            
            if valid_mobile and name:
                results.append({
                    "Company": name,
                    "Category": category,
                    "Mobile": valid_mobile,
                    "Source": "Justdial",
                    "Raw_Phone": valid_mobile # For scoring
                })
        except:
            continue
            
    return results

def scrape_indiamart(category, pincode):
    """Scrape IndiaMART."""
    # IndiaMART search
    # https://dir.indiamart.com/search.mp?ss=BPO&cq=560001
    url = f"https://dir.indiamart.com/search.mp?ss={category}&cq={pincode}"
    
    html = fetch_url(url)
    results = []
    
    if not html:
        return results
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # IndiaMART selectors
    # Listing cards
    cards = soup.select('.lst_cl') or soup.select('.clg')
    
    for card in cards:
        try:
            name_tag = card.select_one('.cname') or card.find('a', class_='cname') or card.find('h4')
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            
            # Phone
            # Often in <span class="pnm"> or similar
            # Sometimes hidden behind "Call Now"
            phone_tag = card.select_one('.pnm') or card.select_one('.duet')
            phone_text = ""
            if phone_tag:
                phone_text = phone_tag.get_text(strip=True)
            else:
                phone_text = card.get_text(" ", strip=True)
                
            phones = re.findall(r'\b[6-9]\d{9}\b', phone_text)
             # Filter valid mobiles
            valid_mobile = None
            for p in phones:
                if is_valid_mobile_string(p):
                    valid_mobile = is_valid_mobile_string(p)
                    break
                    
            if valid_mobile and name:
                results.append({
                    "Company": name,
                    "Category": category,
                    "Mobile": valid_mobile,
                    "Source": "IndiaMART",
                     "Raw_Phone": valid_mobile
                })
        except:
            continue
            
    return results

def scrape_sulekha(category, pincode):
    """Scrape Sulekha."""
    # Sulekha search: https://www.sulekha.com/search/local?q={category}&location={pincode}
    # Sulekha often requires city name. Pincode might redirect.
    url = f"https://www.sulekha.com/search/local?q={category}&location={pincode}"
    
    html = fetch_url(url)
    results = []
    
    if not html:
        return results
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Sulekha selectors
    cards = soup.select('.service-card') or soup.select('.business-item') or soup.select('.listing-item')
    
    if not cards:
        cards = soup.find_all('div', class_=re.compile(r'card|listing'))

    for card in cards:
        try:
            name_tag = card.find('h3') or card.find('a', title=True)
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            
            # Phone: Often requires "View Mobile" click or is in data attributes
            phone_text = card.get_text(" ", strip=True)
            phones = re.findall(r'\b[6-9]\d{9}\b', phone_text)
            
            valid_mobile = None
            for p in phones:
                if is_valid_mobile_string(p):
                    valid_mobile = is_valid_mobile_string(p)
                    break
            
            if valid_mobile and name:
                 results.append({
                    "Company": name,
                    "Category": category,
                    "Mobile": valid_mobile,
                    "Source": "Sulekha",
                     "Raw_Phone": valid_mobile
                })
        except:
            continue
            
    return results

def multi_source_search(pincode, categories):
    """
    Search all sources in parallel.
    """
    all_results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for category in categories:
            futures.append(executor.submit(scrape_justdial, category, pincode))
            futures.append(executor.submit(scrape_indiamart, category, pincode))
            futures.append(executor.submit(scrape_sulekha, category, pincode))
            
        for future in as_completed(futures):
            try:
                data = future.result()
                if data:
                    all_results.extend(data)
            except Exception as e:
                print(f"Scrape error: {e}")
                
    # Deduplicate by Mobile Number (Preferred) or Company Name
    unique_leads = {}
    for lead in all_results:
        # Key by mobile if available, else name
        key = lead['Mobile']
        if key not in unique_leads:
            unique_leads[key] = lead
        else:
            # Merge sources if same mobile found in multiple places
            if lead['Source'] not in unique_leads[key]['Source']:
                unique_leads[key]['Source'] += f", {lead['Source']}"
                
    return list(unique_leads.values())

