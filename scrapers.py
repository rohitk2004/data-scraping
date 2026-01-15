import requests
from bs4 import BeautifulSoup
import re
import json
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
    Validates and cleans phone string.
    NOW: Accepts any valid-looking phone number (Mobile or Landline).
    """
    clean = clean_phone(phone_str)
    if not clean:
        return None
        
    # Handle +91
    if clean.startswith('91') and len(clean) > 10:
        clean = clean[2:]
        
    # Length check: 8 to 12 digits (Landlines can be 11 with 0, Mobiles 10)
    if len(clean) < 8 or len(clean) > 13:
        return None
        
    return clean

def fetch_content_playwright(url):
    """Robust fetch using Playwright with auto-scroll."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=HEADERS['User-Agent'])
            page = context.new_page()
            
            # Go to URL
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except:
                pass # Continue even if timeout, page might have loaded enough
                
            # Scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            
            # Extract Contact Numbers (Click 'Show Number' buttons if found)
            # Justdial specific
            try:
                page.evaluate("""
                    document.querySelectorAll('.callbutton, .contact-number, .pnm, .duet').forEach(b => b.click());
                """)
                page.wait_for_timeout(1000)
            except:
                pass

            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"Playwright error: {e}")
        return None

def extract_from_html_fuzzy(html, source_name, category):
    """
    Scrapes companies using heuristic patterns (Heading + Phone proximity).
    Useful when CSS classes change.
    """
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Split into probable blocks (headings, divs, lis)
    candidates = soup.find_all(['div', 'li', 'article', 'tr'])
    
    seen_mobiles = set()
    
    for card in candidates:
        text = card.get_text(" ", strip=True)
        if len(text) < 20 or len(text) > 1000: # Filter too small/big blocks
            continue
            
        # Check for phone number (Mobile or Landline)
        phones = re.findall(r'(?:\+91|0)?\s?\d{2,5}[\s-]?\d{6,8}', text)
        if not phones:
            phones = re.findall(r'\b\d{8,12}\b', text)
            
        valid_mobile = None
        for p in phones:
            clean = is_valid_mobile_string(p)
            if clean:
                valid_mobile = clean
                break
        
        if valid_mobile and valid_mobile not in seen_mobiles:
            # Found a mobile! Now find the name.
            # Look for checking H tags inside this card or strong/b tags
            name = None
            
            # Strategy A: Heading tag
            head = card.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if head:
                name = head.get_text(strip=True)
                
            # Strategy B: First bold text
            if not name:
                bold = card.find(['b', 'strong'])
                if bold:
                    name = bold.get_text(strip=True)
            
            if name and len(name) > 3 and "search" not in name.lower():
                seen_mobiles.add(valid_mobile)
                results.append({
                    "Company": name,
                    "Category": category,
                    "Mobile": valid_mobile,
                    "Source": source_name,
                    "Raw_Phone": valid_mobile
                })
                
    return results

def google_proxy_search(category, pincode, source_domain, api_key):
    """
    Uses Google (Serper) to find pages on the target site when direct scraping is blocked.
    Query: site:justdial.com "Category" "Pincode"
    """
    url = "https://google.serper.dev/search"
    query = f"site:{source_domain} {category} {pincode}"
    
    payload = json.dumps({
        "q": query,
        "gl": "in",
        "num": 100 # Fetch 100 results per source
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    results = []
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        if "organic" in data:
            for item in data["organic"]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                
                # Combine title and snippet for phone extraction
                full_text = f"{title} {snippet}"
                
                # Extract Phone (Mobile or Landline)
                phones = re.findall(r'(?:\+91|0)?\s?\d{2,5}[\s-]?\d{6,8}', full_text)
                if not phones:
                     phones = re.findall(r'\b\d{8,12}\b', full_text)
                    
                valid_mobile = None
                for p in phones:
                    clean = is_valid_mobile_string(p)
                    if clean:
                        valid_mobile = clean
                        break
                
                # If we found a mobile, Great!
                # If not, we might still want the link to Deep Scrape it later? 
                # For now, let's only keep ones with numbers in snippet to be fast (Zero Cost spirit)
                # Or if the user wants deep research, we can visit the link. 
                # Let's trust the snippet for now.
                
                if valid_mobile:
                    # Clean Company Name (remove " - Justdial" etc)
                    clean_name = title.split(" - ")[0].split(" | ")[0]
                    
                    results.append({
                        "Company": clean_name,
                        "Category": category,
                        "Mobile": valid_mobile,
                        "Source": f"{source_domain} (via Google)",
                        "Raw_Phone": valid_mobile,
                        "Website": link
                    })
    except Exception as e:
        print(f"Google Proxy Error for {source_domain}: {e}")
        
    return results

def scrape_justdial(category, pincode, api_key=None):
    """Scrape Justdial."""
    # 1. Try Google Proxy First (Most reliable for Justdial which blocks brutally)
    if api_key:
        return google_proxy_search(category, pincode, "justdial.com", api_key)

    # 2. Fallback to direct (will likely fail but kept for integrity)
    url = f"https://www.justdial.com/India/Search?q={category}&location={pincode}"
    content = fetch_content_playwright(url)
    if content:
        return extract_from_html_fuzzy(content, "Justdial", category)
    return []

def scrape_indiamart(category, pincode, api_key=None):
    """Scrape IndiaMART."""
    # 1. Try Google Proxy
    results = []
    if api_key:
        results = google_proxy_search(category, pincode, "indiamart.com", api_key)
        if results: return results

    # 2. Direct Search
    url = f"https://dir.indiamart.com/search.mp?ss={category}&cq={pincode}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return extract_from_html_fuzzy(resp.text, "IndiaMART", category)
    except:
        pass
    content = fetch_content_playwright(url)
    if content:
        return extract_from_html_fuzzy(content, "IndiaMART", category)
    return []

def scrape_sulekha(category, pincode, api_key=None):
    """Scrape Sulekha."""
    if api_key:
        results = google_proxy_search(category, pincode, "sulekha.com", api_key)
        if results: return results

    url = f"https://www.sulekha.com/search/local?q={category}&location={pincode}"
    content = fetch_content_playwright(url)
    if content:
        return extract_from_html_fuzzy(content, "Sulekha", category)
    return []

def scrape_google_places(category, pincode, api_key):
    """
    Uses Serper Places API (Google Maps) - High Reliability Source.
    """
    if not api_key: 
        return []
        
    results = []
    url = "https://google.serper.dev/places"
    # Try 2 pages to get up to 40 results
    for page in range(1, 3):
        payload = json.dumps({
            "q": f"{category} in {pincode}",
            "location": f"{pincode}, India",
            "page": page
        })
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            data = response.json()
            places = data.get("places", [])
            
            if not places:
                break
                
            for place in places:
                phone = place.get("phoneNumber")
                
                # Validation
                valid_mobile = None
                if phone:
                    valid_mobile = is_valid_mobile_string(phone)
                    
                if valid_mobile:
                     results.append({
                        "Company": place.get("title"),
                        "Category": category,
                        "Mobile": valid_mobile,
                        "Source": "Google Maps",
                        "Raw_Phone": valid_mobile,
                        "Website": place.get("website", "N/A")
                    })
        except Exception as e:
            print(f"Places API Error: {e}")
            
    return results

def multi_source_search(pincode, categories, api_key=None):
    """
    Search all sources in parallel: Justdial, IndiaMART, Sulekha, and Google Maps.
    """
    all_results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for cat in categories:
            # Add JD/IM/Sulekha
            futures.append(executor.submit(scrape_justdial, cat, pincode, api_key))
            futures.append(executor.submit(scrape_indiamart, cat, pincode, api_key))
            futures.append(executor.submit(scrape_sulekha, cat, pincode, api_key))
            # Add Google Places (New Robust Source)
            futures.append(executor.submit(scrape_google_places, cat, pincode, api_key))
            
        for future in as_completed(futures):
            try:
                data = future.result()
                if data:
                    all_results.extend(data)
            except Exception as e:
                pass
                
    # Deduplicate
    unique_leads = {}
    for lead in all_results:
        key = lead['Mobile']
        if key not in unique_leads:
            unique_leads[key] = lead
        else:
             if lead['Source'] not in unique_leads[key]['Source']:
                unique_leads[key]['Source'] += f", {lead['Source']}"
                
    return list(unique_leads.values())

