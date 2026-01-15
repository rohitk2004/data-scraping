import streamlit as st
import pandas as pd
import requests
import json
import time
import random
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapers import multi_source_search


# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Company Data Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hidden API Key (Not shown in UI)
SERPER_API_KEY = "fafa9ba8f3e9438106a8a70c29a84f2538597fea"

# ==========================================
# CUSTOM CSS - BLUE & WHITE PROFESSIONAL THEME
# ==========================================
st.markdown("""
<style>
    /* High Contrast / Ultra Clean Theme */
    
    /* Global Styles */
    body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #ffffff;
        color: #000000 !important; /* Force Black Text */
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }
    
    h1 {
        border-bottom: 2px solid #000;
        padding-bottom: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f4f4f5; /* Very Light Gray */
        border-right: 1px solid #d4d4d8;
    }
    
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    
    /* Input Fields */
    .stTextInput input {
        border: 1px solid #000000;
        border-radius: 4px;
        padding: 0.5rem;
        color: #000000;
        background-color: #ffffff;
    }
    
    .stTextInput input:focus {
        border-color: #000000;
        box-shadow: 0 0 0 1px #000000;
    }
    
    .stTextInput label {
        color: #000000 !important;
        font-weight: 600;
    }
    
    /* Buttons */
    /* Buttons */
    /* Buttons */
    .stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc;
        border-radius: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: none;
    }
    
    .stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #cccccc !important;
    }
    
    /* Primary Button Override (Start Discovery, Enrich) */
    /* Check for Streamlit's primary button class injection or use attribute selector */
    div[data-testid="stForm"] .stButton > button,
    button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: #ffffff !important;
        border: none !important;
    }
    
    div[data-testid="stForm"] .stButton > button:hover,
    button[kind="primary"]:hover {
        background-color: #ff4b4b !important;
        color: #ffffff !important;
        box-shadow: none !important;
    }
    
    /* Result Cards */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border: 1px solid #e5e5e5; /* Subtle border */
        border-radius: 0px; /* Sharp corners */
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: none !important; /* Flat look */
    }

    /* Paragraphs and Text */
    p, li, span, div {
        color: #000000;
        line-height: 1.5;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: 800;
    }
    
    [data-testid="stMetricLabel"] {
        color: #000000 !important;
        opacity: 0.7;
    }
    
    /* Links */
    a {
        color: #000000 !important;
        text-decoration: underline;
        font-weight: 600;
    }
    
    /* Tier Badge */
    
    /* Divider */
    hr {
        border-color: #000000;
        opacity: 0.1;
        margin: 2rem 0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #000000 !important;
        font-weight: 600;
        background-color: #f9f9f9;
        border: 1px solid #ddd;
    }
    
    /* Form Label Help */
    [data-testid="stForm"] {
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# API FUNCTIONS
# ==========================================

# Mobile validation moved to scrapers.py, but keeping a helper here if needed for UI
def is_valid_mobile_display(phone):
    return True if phone and len(str(phone)) == 10 else False

def get_50_companies_from_serper(pincode, api_key):
    """
    Fetches companies using specific High-Pain HCM categories.
    """
    all_results = []
    seen_ids = set()
    
    categories = [
        "BPO companies",
        "Construction firms", 
        "Private Hospitals",
        "Manufacturing units"
    ]
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
def discover_companies(pincode):
    """
    Uses the Multi-Source Scraper (Justdial, IndiaMART, Sulekha).
    """
    categories = ["BPO", "Corporate House", "Hospital", "Manufacturing", "Manpower"]
    
    with st.spinner(f"🕵️ Searching across Justdial, IndiaMART, and Sulekha for {pincode}..."):
         # Pass API Key for Google Proxy fallback
         results = multi_source_search(pincode, categories, SERPER_API_KEY)
         
    return results

def is_small_retail_shop(company):
    # ... existing implementation ...
    return False # Temporarily disabled to ensure we show results if found


def get_zauba_directors(company_name, api_key):
    """
    Extracts director names directly from Google Snippets.
    Updated for robust Zauba patterns.
    """
    directors = []
    
    # Query 1: ZaubaCorp specific
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"{company_name} directors site:zaubacorp.com",
        "gl": "in"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        if "organic" in data:
            for item in data["organic"][:3]:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                text = f"{title} {snippet}"
                
                # Pattern A: "Directors of ... are Name1, Name2"
                if "are" in text and "Directors of" in text:
                     parts = text.split(" are ")[-1].split(".")[0].split(",")
                     for p in parts:
                         clean = p.replace("and", "").strip()
                         if len(clean) > 3: directors.append(clean)
                         
                # Pattern B: Zauba Table "DIN · NAME, Director"
                # Looks for:  06413133 · PARAG ALLAWADI, Director
                matches = re.findall(r'·\s([A-Z\s]+),\sDirector', text)
                if matches:
                    directors.extend([m.strip() for m in matches])
                    
    except:
        pass
        
    # Query 2: Generic "Owner/Director" search if Zauba fails
    if not directors:
        try:
            payload = json.dumps({
                "q": f"{company_name} owner director linkedin",
                "gl": "in"
            })
            response = requests.request("POST", url, headers=headers, data=payload)
            data = response.json()
            if "organic" in data:
                 for item in data["organic"][:2]:
                     title = item.get("title", "")
                     # accepted patterns: "Name - Director - Company"
                     if " - " in title:
                         parts = title.split(" - ")
                         for part in parts:
                             if part.strip() not in [company_name, "Director", "Owner", "Profile", "LinkedIn"] and len(part.split()) < 4:
                                 if part.strip() not in directors:
                                     directors.append(part.strip())
                                     break
        except:
             pass

    # Clean duplicates
    unique_directors = []
    for d in directors:
        d_clean = re.sub(r'[^a-zA-Z\s]', '', d).strip()
        if d_clean and d_clean not in unique_directors and len(d_clean) > 3:
            unique_directors.append(d_clean)
            
    return unique_directors[:3]

def get_startup_india_founders(company_name, api_key):
    """
    Search Startup India for Founder details if potential startup.
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"site:startupindia.gov.in {company_name} founder",
        "gl": "in"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    founders = []
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if "organic" in data:
            for item in data["organic"][:2]:
                snippet = item.get("snippet", "")
                # Simple extraction: Look for names after keywords
                # This is heuristic
                if "Founder" in snippet or "Director" in snippet:
                    founders.append(item.get("title").split("-")[0].strip())
    except:
        pass
    return list(set(founders))

def find_website(company_name, api_key):
    """Finds website if missing."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"{company_name} official website",
        "gl": "in"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if "organic" in data and len(data["organic"]) > 0:
            link = data["organic"][0]["link"]
            if "justdial" not in link and "indiamart" not in link and "sulekha" not in link:
                return link
    except:
        pass
    return "N/A"



# ==========================================
# CORE LOGIC
# ==========================================

def enrich_single_company(company):
    """
    Performs deep research on a single company:
    1. Find Website
    2. Find Directors (Zauba)
    3. Find Founders (Startup India)
    4. Calculate Score
    """
    # 1. Find Website
    company["Website"] = find_website(company['Company'], SERPER_API_KEY)
    
    # 2. Get Directors (ZaubaCorp)
    directors = get_zauba_directors(company['Company'], SERPER_API_KEY)
    
    # 3. Get Founders (Startup India) - if needed
    if not directors:
        founders = get_startup_india_founders(company['Company'], SERPER_API_KEY)
        if founders:
             directors.extend(founders)
             company["Startup"] = True
    
    company["Directors"] = directors
    
    return company

def search_and_process(pincode):
    """
    1. Scrape Basic Data (Multi-Source)
    2. Enrich ALL Data (Parallel)
    """
    # Phase 1: Discovery
    status_box = st.status("🕵️ Phase 1: Scouting Companies...", expanded=True)
    
    categories = ["BPO", "Corporate House", "Hospital", "Manufacturing", "Manpower"]
    raw_leads = multi_source_search(pincode, categories, SERPER_API_KEY)
    
    if not raw_leads:
        status_box.update(label="⚠️ No companies found.", state="error")
        return []
        
    status_box.update(label=f"✅ Found {len(raw_leads)} companies! Starting Deep Research...", state="running")
    
    # Phase 2: Deep Enrichment
    enriched_results = []
    total = len(raw_leads)
    progress_bar = status_box.progress(0, text="Extracting Directors & Websites...")
    
    # Parallel Enrichment
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(enrich_single_company, company): company for company in raw_leads}
        
        completed_count = 0
        for future in as_completed(futures):
            try:
                result = future.result()
                enriched_results.append(result)
            except Exception as e:
                # If enrichment fails, just keep basic data
                enriched_results.append(futures[future])
                
            completed_count += 1
            progress_bar.progress(completed_count / total, text=f"Researched {completed_count}/{total} companies...")
            
    status_box.update(label="🚀 Mission Complete! All data ready.", state="complete", expanded=False)
    return enriched_results

# ==========================================
# STREAMLIT UI
# ==========================================

# Sidebar
with st.sidebar:
    st.markdown("### 📍 Search Settings")
    st.markdown("")
    
    with st.form(key='search_form'):
        pincode = st.text_input(
            "Enter Pincode",
            value="110017",
            placeholder="Enter pincode",
            help="Enter the pincode to search and enrich companies"
        )
        
        st.markdown("")
        submit_button = st.form_submit_button("🚀 Start Master Search", type="primary")

    if submit_button:
        if not pincode:
            st.error("⚠️ Please enter a Pincode.")
        else:
            # Clear previous state
            if "results" in st.session_state:
                del st.session_state["results"]
                
            data = search_and_process(pincode)
            st.session_state["results"] = data
            st.session_state["pincode"] = pincode
            # st.rerun() # No need to rerun, just continue render

    st.markdown("")
    st.divider()
    st.markdown("### ℹ️ How it Works")
    st.markdown("""
    1. **Scrape**: Jussdial, IndiaMART, Sulekha, Google Maps.
    2. **Enrich**: Automatically finds **Directors** & **Websites** for EVERY company.
    3. **Deliver**: One single list with all details.
    """)

# Main Content Area
if "results" not in st.session_state:
    st.markdown("")
    st.markdown("")
    st.markdown("<h1 style='text-align: center; color: #1e40af;'>Zero-Cost Master Lead Engine 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>One click to find Companies, Mobiles, Directors & Websites.</p>", unsafe_allow_html=True)
    
else:
    # Results Display
    results = st.session_state["results"]
    pincode = st.session_state.get("pincode", "")
    
    if not results:
        st.warning(f"No results found for {pincode}.")
    else:
        st.markdown(f"### 💎 Master Lead List: {pincode} ({len(results)} Leads)")
        
        # CSV Export Logic
        df_export = pd.DataFrame(results)
        # Flatten lists for CSV
        df_export["Directors"] = df_export["Directors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        
        csv = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=f"📥 Download Full Report ({len(results)} Companies)",
            data=csv,
            file_name=f'Master_Leads_{pincode}_{int(time.time())}.csv',
            mime='text/csv',
            type="primary"
        )
        
        st.divider()
        
        # Detailed List View
        for company in results:
            with st.container():
                # Card Layout
                # Card Layout
                st.subheader(company['Company'])
                st.caption(f"Source: {company.get('Source', 'Unknown')}")
                
                # Details Grid
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**📱 Mobile:** `{company.get('Mobile')}`")
                    st.markdown(f"**🏷️ Category:** {company.get('Category')}")
                    
                with col2:
                    website = company.get('Website')
                    if website and website != "N/A":
                        st.markdown(f"**🌐 Website:** [Link]({website})")
                    else:
                        st.markdown("**🌐 Website:** N/A")
                        
                with col3:
                    directors = company.get('Directors', [])
                    if directors:
                        st.markdown("**🕴️ Directors/Founders:**")
                        for d in directors:
                            st.text(f"• {d}")
                    else:
                        st.markdown("**🕴️ Directors:** Not Found")
                
                st.divider()


