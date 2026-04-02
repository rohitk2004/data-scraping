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
    page_title="LeadForge — Smart Company Discovery",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hidden API Key (Not shown in UI)
SERPER_API_KEY = "7c2d5e0803bea51ff089a6457a1d849eb5b48ceb"

# ==========================================
# PREMIUM CSS — DARK GLASSMORPHISM THEME
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
    /* ─── Root Variables ─── */
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-card: rgba(17, 24, 39, 0.6);
        --bg-glass: rgba(255, 255, 255, 0.04);
        --border-glass: rgba(255, 255, 255, 0.08);
        --border-hover: rgba(255, 255, 255, 0.15);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-1: #6366f1;     /* Indigo */
        --accent-2: #8b5cf6;     /* Violet */
        --accent-3: #06b6d4;     /* Cyan */
        --accent-4: #10b981;     /* Emerald */
        --accent-gradient: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
        --accent-gradient-warm: linear-gradient(135deg, #f59e0b, #ef4444, #ec4899);
        --shadow-glow: 0 0 40px rgba(99, 102, 241, 0.1);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
    }

    /* ─── Global Styles ─── */
    body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stApp {
        background: linear-gradient(180deg, #0a0e1a 0%, #0f172a 40%, #0a0e1a 100%) !important;
    }

    /* Ambient gradient blobs */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: -20%;
        right: -10%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    [data-testid="stAppViewContainer"]::after {
        content: '';
        position: fixed;
        bottom: -15%;
        left: -10%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.06) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* ─── Headers ─── */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    h1, .stMarkdown h1 {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }

    /* ─── Sidebar ─── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0f172a 100%) !important;
        border-right: 1px solid var(--border-glass) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] .stMarkdown h3 {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em;
    }

    /* ─── Input Fields ─── */
    .stTextInput > div > div > input {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--accent-1) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15), var(--shadow-glow) !important;
    }

    .stTextInput label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    /* ─── Buttons ─── */
    .stButton > button {
        background: var(--bg-glass) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-md) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: var(--border-hover) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    /* Primary Button */
    div[data-testid="stForm"] .stButton > button,
    button[kind="primary"],
    .stDownloadButton > button {
        background: var(--accent-gradient) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 25px rgba(99, 102, 241, 0.3) !important;
    }

    div[data-testid="stForm"] .stButton > button:hover,
    button[kind="primary"]:hover,
    .stDownloadButton > button:hover {
        box-shadow: 0 6px 35px rgba(99, 102, 241, 0.45) !important;
        transform: translateY(-2px) !important;
    }

    /* ─── Forms ─── */
    [data-testid="stForm"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(12px) !important;
    }

    /* ─── Metrics ─── */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-family: 'Inter', sans-serif !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    /* ─── Links ─── */
    a {
        color: var(--accent-3) !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        transition: color 0.2s ease !important;
    }

    a:hover {
        color: var(--accent-2) !important;
    }

    /* ─── Paragraphs and Text ─── */
    p, li, span {
        color: var(--text-secondary);
        line-height: 1.7;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--text-muted) !important;
    }

    /* ─── Dividers ─── */
    hr {
        border-color: var(--border-glass) !important;
        opacity: 1 !important;
        margin: 1.5rem 0 !important;
    }

    /* ─── Expander ─── */
    .streamlit-expanderHeader {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-md) !important;
    }

    /* ─── Status / Spinner ─── */
    [data-testid="stStatusWidget"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-lg) !important;
        backdrop-filter: blur(8px) !important;
    }

    /* ─── Progress bar ─── */
    .stProgress > div > div > div {
        background: var(--accent-gradient) !important;
        border-radius: 20px !important;
    }

    /* ─── Custom Hero Section ─── */
    .hero-container {
        text-align: center;
        padding: 4rem 2rem 3rem;
        position: relative;
    }

    .hero-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 100px;
        padding: 0.4rem 1.2rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #818cf8;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        animation: fadeInDown 0.6s ease;
    }

    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        line-height: 1.1;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 30%, #6366f1 60%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: fadeInUp 0.8s ease;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 400;
        max-width: 550px;
        margin: 0 auto 2rem;
        line-height: 1.6;
        animation: fadeInUp 1s ease;
    }

    .hero-features {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        animation: fadeInUp 1.2s ease;
    }

    .hero-feature {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 100px;
        padding: 0.5rem 1.2rem;
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 500;
        backdrop-filter: blur(4px);
        transition: all 0.3s ease;
    }

    .hero-feature:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: rgba(99, 102, 241, 0.06);
        color: #c7d2fe;
        transform: translateY(-2px);
    }

    .feature-icon {
        font-size: 1rem;
    }

    /* ─── Company Card ─── */
    .company-card {
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .company-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--accent-gradient);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .company-card:hover {
        border-color: rgba(99, 102, 241, 0.2);
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3), 0 0 40px rgba(99, 102, 241, 0.05);
        transform: translateY(-2px);
    }

    .company-card:hover::before {
        opacity: 1;
    }

    .company-name {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.25rem;
        letter-spacing: -0.01em;
    }

    .company-source {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 1.2rem;
    }

    .source-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--accent-4);
        display: inline-block;
    }

    .detail-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.2rem;
    }

    @media (max-width: 768px) {
        .detail-grid {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 2rem;
        }
    }

    .detail-item {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
    }

    .detail-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .detail-value {
        font-size: 0.9rem;
        color: #e2e8f0;
        font-weight: 500;
    }

    .detail-value.phone {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        color: #818cf8;
        font-weight: 600;
    }

    .detail-value.website a {
        color: #22d3ee !important;
        word-break: break-all;
    }

    .director-chip {
        display: inline-block;
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 100px;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        color: #c4b5fd;
        font-weight: 500;
        margin: 0.15rem 0.2rem;
    }

    /* ─── Results Header ─── */
    .results-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }

    .results-count {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 100px;
        padding: 0.35rem 1rem;
        font-size: 0.8rem;
        color: #34d399;
        font-weight: 600;
    }

    /* ─── Sidebar Info Cards ─── */
    .info-step {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding: 0.75rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        transition: all 0.2s ease;
    }

    .info-step:hover {
        border-color: rgba(99, 102, 241, 0.15);
        background: rgba(99, 102, 241, 0.04);
    }

    .step-number {
        width: 24px;
        height: 24px;
        min-width: 24px;
        border-radius: 50%;
        background: var(--accent-gradient);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 700;
        color: white;
    }

    .step-text {
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    .step-text strong {
        color: #e2e8f0;
    }

    /* ─── Keyframe Animations ─── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ─── Scrollbar ─── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* ─── Hide Streamlit Branding ─── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# API FUNCTIONS
# ==========================================

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
         results = multi_source_search(pincode, categories, SERPER_API_KEY)
         
    return results

def is_small_retail_shop(company):
    return False

def get_zauba_directors(company_name, api_key):
    """
    Extracts director names directly from Google Snippets.
    """
    directors = []
    
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
                
                if "are" in text and "Directors of" in text:
                     parts = text.split(" are ")[-1].split(".")[0].split(",")
                     for p in parts:
                         clean = p.replace("and", "").strip()
                         if len(clean) > 3: directors.append(clean)
                         
                matches = re.findall(r'·\s([A-Z\s]+),\sDirector', text)
                if matches:
                    directors.extend([m.strip() for m in matches])
                    
    except:
        pass
        
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
                     if " - " in title:
                         parts = title.split(" - ")
                         for part in parts:
                             if part.strip() not in [company_name, "Director", "Owner", "Profile", "LinkedIn"] and len(part.split()) < 4:
                                 if part.strip() not in directors:
                                     directors.append(part.strip())
                                     break
        except:
             pass

    unique_directors = []
    for d in directors:
        d_clean = re.sub(r'[^a-zA-Z\s]', '', d).strip()
        if d_clean and d_clean not in unique_directors and len(d_clean) > 3:
            unique_directors.append(d_clean)
            
    return unique_directors[:3]

def get_startup_india_founders(company_name, api_key):
    """
    Search Startup India for Founder details.
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

def get_employee_count(company_name, api_key):
    """
    Searches Google for LinkedIn employee count.
    """
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"{company_name} linkedin employee count",
        "gl": "in"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        organic = data.get("organic", [])
        if not organic:
            return None, "", None
            
        result = organic[0]
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        link = result.get("link", "")
        full_text = snippet + " " + title
        
        emp_count = None
        match = re.search(r"([\d,]+)(?:\+|-\d+)?\s+employees", full_text, re.IGNORECASE)
        if match:
            count_str = match.group(1).replace(',', '')
            try:
                emp_count = int(count_str)
            except ValueError:
                emp_count = None
        
        return emp_count, snippet, link
        
    except Exception as e:
        return None, "", None

def enrich_single_company(company):
    """
    Performs deep research on a single company.
    """
    company["Website"] = find_website(company['Company'], SERPER_API_KEY)
    
    directors = get_zauba_directors(company['Company'], SERPER_API_KEY)
    
    if not directors:
        founders = get_startup_india_founders(company['Company'], SERPER_API_KEY)
        if founders:
             directors.extend(founders)
             company["Startup"] = True
    
    company["Directors"] = directors

    emp_count, _, _ = get_employee_count(company['Company'], SERPER_API_KEY)
    company["Employees"] = emp_count if emp_count else "N/A"
    
    return company

def search_and_process(pincode):
    """
    1. Scrape Basic Data (Multi-Source)
    2. Enrich ALL Data (Parallel)
    """
    status_box = st.status("⚡ Phase 1: Scouting Companies...", expanded=True)
    
    categories = ["BPO", "Corporate House", "Hospital", "Manufacturing", "Manpower"]
    raw_leads = multi_source_search(pincode, categories, SERPER_API_KEY)
    
    if not raw_leads:
        status_box.update(label="⚠️ No companies found.", state="error")
        return []
        
    status_box.update(label=f"✅ Found {len(raw_leads)} companies! Starting Deep Research...", state="running")
    
    enriched_results = []
    total = len(raw_leads)
    progress_bar = status_box.progress(0, text="Extracting Directors & Websites...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(enrich_single_company, company): company for company in raw_leads}
        
        completed_count = 0
        for future in as_completed(futures):
            try:
                result = future.result()
                enriched_results.append(result)
            except Exception as e:
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
    st.markdown("")
    st.markdown("### ⚡ LeadForge")
    st.markdown('<p style="color: #64748b; font-size: 0.8rem; margin-top: -0.5rem;">Smart Company Discovery Engine</p>', unsafe_allow_html=True)
    st.markdown("")
    
    with st.form(key='search_form'):
        pincode = st.text_input(
            "PINCODE",
            value="110017",
            placeholder="Enter target pincode",
            help="Enter a 6-digit Indian pincode to discover companies"
        )
        
        st.markdown("")
        submit_button = st.form_submit_button("⚡ Launch Discovery", type="primary")

    if submit_button:
        if not pincode:
            st.error("⚠️ Please enter a Pincode.")
        else:
            if "results" in st.session_state:
                del st.session_state["results"]
                
            data = search_and_process(pincode)
            st.session_state["results"] = data
            st.session_state["pincode"] = pincode

    st.markdown("")
    st.divider()
    st.markdown("### 🧭 How It Works")
    st.markdown("")
    
    st.markdown("""
    <div class="info-step">
        <div class="step-number">1</div>
        <div class="step-text"><strong>Scrape</strong> — Multi-source crawl across JustDial, IndiaMART, Sulekha & Google Maps</div>
    </div>
    <div class="info-step">
        <div class="step-number">2</div>
        <div class="step-text"><strong>Enrich</strong> — Auto-extract Directors, Websites & Employee counts via ZaubaCorp & LinkedIn</div>
    </div>
    <div class="info-step">
        <div class="step-number">3</div>
        <div class="step-text"><strong>Deliver</strong> — Download a single CSV with every lead fully enriched</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    st.divider()
    st.markdown('<p style="color: #334155; font-size: 0.7rem; text-align: center;">Built with ❤️ by LeadForge</p>', unsafe_allow_html=True)


# Main Content Area
if "results" not in st.session_state:
    # Hero Section
    st.markdown("""
    <div class="hero-container">
        <div class="hero-badge">⚡ Zero-Cost Lead Intelligence</div>
        <div class="hero-title">Discover Companies.<br>Extract Contacts.<br>Close Deals.</div>
        <div class="hero-subtitle">
            Enter any Indian pincode and instantly get a comprehensive lead list with mobile numbers, 
            directors, websites & employee counts — all from one search.
        </div>
        <div class="hero-features">
            <div class="hero-feature">
                <span class="feature-icon">🔍</span> Multi-Source Scraping
            </div>
            <div class="hero-feature">
                <span class="feature-icon">🕴️</span> Director Extraction
            </div>
            <div class="hero-feature">
                <span class="feature-icon">📊</span> LinkedIn Enrichment
            </div>
            <div class="hero-feature">
                <span class="feature-icon">📥</span> CSV Export
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
else:
    # Results Display
    results = st.session_state["results"]
    pincode = st.session_state.get("pincode", "")
    
    if not results:
        st.warning(f"No results found for {pincode}.")
    else:
        # Results Header
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
            <div>
                <h2 style="margin: 0; font-size: 1.5rem;">Lead Intelligence Report</h2>
                <p style="color: #64748b; margin: 0.25rem 0 0; font-size: 0.85rem;">Pincode: {pincode}</p>
            </div>
            <div class="results-count">
                <span>●</span> {len(results)} Companies Found
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # CSV Export
        df_export = pd.DataFrame(results)
        df_export["Directors"] = df_export["Directors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        csv = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=f"📥 Download Full Report — {len(results)} Companies",
            data=csv,
            file_name=f'LeadForge_{pincode}_{int(time.time())}.csv',
            mime='text/csv',
            type="primary"
        )
        
        st.markdown("")
        
        # Company Cards
        for i, company in enumerate(results):
            # Build directors HTML
            directors = company.get('Directors', [])
            if directors:
                directors_html = "".join([f'<span class="director-chip">{d}</span>' for d in directors])
            else:
                directors_html = '<span style="color: #475569; font-size: 0.85rem;">Not Found</span>'
            
            # Website HTML
            website = company.get('Website')
            if website and website != "N/A":
                domain = website.replace("https://", "").replace("http://", "").split("/")[0]
                website_html = f'<a href="{website}" target="_blank">{domain}</a>'
            else:
                website_html = '<span style="color: #475569;">N/A</span>'

            # Employees
            employees = company.get('Employees', 'N/A')

            st.markdown(f"""
            <div class="company-card">
                <div class="company-name">{company['Company']}</div>
                <div class="company-source">
                    <span class="source-dot"></span>
                    {company.get('Source', 'Unknown')} &nbsp;·&nbsp; {company.get('Category', '')}
                </div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">📱 Mobile</div>
                        <div class="detail-value phone">{company.get('Mobile', 'N/A')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">🌐 Website</div>
                        <div class="detail-value website">{website_html}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">👥 Employees</div>
                        <div class="detail-value">{employees}</div>
                    </div>
                </div>
                <div style="margin-top: 1rem;">
                    <div class="detail-label" style="margin-bottom: 0.4rem;">🕴️ Directors / Founders</div>
                    {directors_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
