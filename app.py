import streamlit as st
import pandas as pd
import requests
import json
import time
import random
import re
from bs4 import BeautifulSoup
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
    .stButton > button {
        background-color: #000000;
        color: #ffffff !important;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: opacity 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #333333;
        color: #ffffff !important;
        border-color: #000000;
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
    .tier-badge {
        background-color: #000000;
        color: #ffffff !important;
        padding: 4px 8px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    
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
    Scrapes director names from ZaubaCorp.
    """
    # Step 1: Find URL
    search_url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f"site:zaubacorp.com {company_name}",
        "gl": "in"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    target_url = None
    
    try:
        response = requests.request("POST", search_url, headers=headers, data=payload)
        data = response.json()
        if "organic" in data and len(data["organic"]) > 0:
            target_url = data["organic"][0]["link"]
    except Exception as e:
        return []

    if not target_url:
        return []
        
    # Step 2: Scrape Page
    try:
        scrape_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        page_response = requests.get(target_url, headers=scrape_headers, timeout=10)
        soup = BeautifulSoup(page_response.content, 'lxml')
        
        directors = []
        
        # Look for table rows containing "Director"
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                text_content = [c.get_text(strip=True) for c in cols]
                for text in text_content:
                    if any(x in text.lower() for x in ['director', 'managing', 'whole-time']):
                         for col_text in text_content:
                             if len(col_text) > 3 and col_text.replace(' ', '').isalpha() and not any(k in col_text.lower() for k in ['director', 'din', 'appointment']):
                                 if col_text not in directors:
                                     directors.append(col_text)
                                     
        # Fallback: Look for "Signatory Details"
        h5_tags = soup.find_all('h5', string=re.compile('Signatory Details'))
        if h5_tags:
            parent = h5_tags[0].find_parent('div')
            if parent:
                parent_table = parent.find_next('table')
                if parent_table:
                    d_rows = parent_table.find_all('tr')
                    for dr in d_rows[1:]: 
                        dcs = dr.find_all('td')
                        if len(dcs) >= 2:
                            name = dcs[1].get_text(strip=True)
                            if name and name not in directors:
                                directors.append(name)
                                
        return directors[:3] 
    except Exception as e:
        return []

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

def get_employee_count(company_name, api_key):
    """
    Searches Google for LinkedIn employee count.
    Returns: (count, snippet_text, linkedin_url)
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
        
        # Extract employee count
        emp_count = None
        import re
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


def reveal_director_contact(director_name, company_name, api_key):
    """Searches for mobile number or contact info for a specific director."""
    query = f"{director_name} {company_name} mobile phone number contact"
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "gl": "in"
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        snippets = []
        if "organic" in data:
            for item in data["organic"][:3]: # Top 3 results
                snippets.append({
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "link": item.get("link")
                })
        return snippets
    except:
        return []

def calculate_lead_score(company):
    """
    Assign a "Gold Medal" to leads that have a Mobile Number, a Director Name, and a Website.
    """
    mobile = company.get('Mobile')
    directors = company.get('Directors', [])
    website = company.get('Website')
    
    score = 0
    messages = []
    
    # Prerequisite: Mobile (already guaranteed by scraper, but checking)
    if mobile and mobile != "N/A":
        score += 1
        
    # Director
    if directors and len(directors) > 0:
        score += 1
        
    # Website
    if website and website != "N/A":
        score += 1
        
    # Gold Medal Condition: All 3 present
    if score == 3:
        return "🥇 GOLD MEDAL"
    elif score == 2:
        return "🥈 Silver"
    else:
        return "🥉 Bronze"

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
            value="560001",
            placeholder="Enter pincode",
            help="Enter the pincode to search for companies"
        )
        
        st.markdown("")
        submit_button = st.form_submit_button("🚀 Start Discovery", type="primary")

    if submit_button:
        if not pincode:
            st.error("⚠️ Please enter a Pincode.")
        else:
            # Clear previous state
            if "discovered_data" in st.session_state:
                del st.session_state["discovered_data"]
            if "enriched_data" in st.session_state:
                del st.session_state["enriched_data"]
                
            companies = discover_companies(pincode)
                
            if not companies:
                st.warning(f"⚠️ No companies found in {pincode} related to HCM categories.")
            else:
                st.session_state["discovered_data"] = companies
                st.session_state["pincode"] = pincode
                st.rerun()

    st.markdown("")
    st.divider()
    st.markdown("### ℹ️ How it Works")
    st.markdown("""
    1. **Data Sources**: Simultaneous search on **Justdial, IndiaMART, Sulekha**.
    2. **Validation**: **All Valid Phone Numbers** (Mobile & Landline) are captured.
    3. **Deep Research**: Visits **ZaubaCorp** & **Startup India** to find Directors/Founders.
    4. **Scoring**: 🥇 **Gold Medal** assigned if Leads have Phone + Director + Website.
    """)

# Main Content Area

# State: Landing Page
if "discovered_data" not in st.session_state and "enriched_data" not in st.session_state:
    st.markdown("")
    st.markdown("")
    st.markdown("<h1 style='text-align: center; color: #1e40af;'>Zero-Cost Master Lead Engine 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Find HCM Sales Leads with Direct Mobile Numbers.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <h3>🎯 Ready to hunt?</h3>
            <p style="color: #64748b; margin-bottom: 1.5rem;">Enter a pincode to scrape Justdial, IndiaMART, and Sulekha instantly.</p>
            <div style="background-color: #f1f5f9; padding: 0.75rem; border-radius: 8px; font-size: 0.9rem; color: #475569;">
                👈 <strong>Start in the Sidebar</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

# State: Discovery Results (Selection Phase)
elif "discovered_data" in st.session_state and "enriched_data" not in st.session_state:
    data = st.session_state["discovered_data"]
    pincode_display = st.session_state.get("pincode", "")
    
    st.markdown(f"### 📋 Discovered Leads in {pincode_display}")
    st.info(f"Found {len(data)} unique companies with valid mobile numbers.")
    
    # Create a DataFrame for selection
    df_discovery = pd.DataFrame(data)
    
    # CSV Download for ALL Discovered Leads
    csv_discovery = df_discovery.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download All Discovered Leads (CSV)",
        data=csv_discovery,
        file_name=f'all_leads_{pincode_display}_{int(time.time())}.csv',
        mime='text/csv'
    )
    
    # Add a selection column (default True for top 10)
    df_discovery.insert(0, "Enrich", False)
    for idx in df_discovery.index[:10]:
        df_discovery.at[idx, "Enrich"] = True
        
    # Display editable dataframe
    edited_df = st.data_editor(
        df_discovery,
        column_config={
            "Enrich": st.column_config.CheckboxColumn(
                "Enrich?",
                help="Select to find Directors & Website",
                default=False,
            ),
            "Company": st.column_config.TextColumn("Company"),
            "Category": st.column_config.TextColumn("Category"),
            "Mobile": st.column_config.TextColumn("Mobile"),
            "Source": st.column_config.TextColumn("Source"),
        },
        disabled=["Company", "Category", "Mobile", "Source"],
        hide_index=True,
        use_container_width=True
    )
    
    # Button to proceed
    selected_indices = edited_df[edited_df["Enrich"]].index
    num_selected = len(selected_indices)
    
    if st.button(f"✨ Deep Research {num_selected} Companies", type="primary"):
        if num_selected == 0:
            st.error("Please select at least one company.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            enriched_companies = []
            
            # Loop through selected companies
            for i, idx in enumerate(selected_indices):
                company = data[idx]
                status_text.text(f"Researching {i+1}/{num_selected}: {company['Company']}...")
                
                # 1. Find Website (if missing)
                company["Website"] = find_website(company['Company'], SERPER_API_KEY)
                
                # 2. Get Directors (ZaubaCorp)
                directors = get_zauba_directors(company['Company'], SERPER_API_KEY)
                
                # 3. Get Founders (Startup India) if no directors found or just to augment
                if not directors:
                    founders = get_startup_india_founders(company['Company'], SERPER_API_KEY)
                    if founders:
                         directors.extend(founders)
                         company["Startup"] = True
                
                company["Directors"] = directors
                
                # 4. Calculate Score
                company["Score"] = calculate_lead_score(company)
                
                enriched_companies.append(company)
                progress_bar.progress((i + 1) / num_selected)
                
            st.session_state["enriched_data"] = enriched_companies
            st.rerun()

# State: Enriched Results
elif "enriched_data" in st.session_state:
    enriched = st.session_state["enriched_data"]
    
    st.markdown("### 💎 Master Lead List")
    
    if st.button("⬅️ Back"):
        del st.session_state["enriched_data"]
        st.rerun()
        
    st.divider()
    
    # Custom List View
    for company in enriched:
        with st.container():
            # Header
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                 st.subheader(company['Company'])
                 st.caption(f"Source: {company.get('Source', 'Unknown')}")
            with c2:
                st.markdown(f"### {company.get('Score', '')}")
            
            # Details
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
            
    # Export
    df_export = pd.DataFrame(enriched)
    # Flatten lists
    df_export["Directors"] = df_export["Directors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Master Leads CSV",
        data=csv,
        file_name=f'master_leads_{int(time.time())}.csv',
        mime='text/csv'
    )


