import streamlit as st
import pandas as pd
import requests
import json
import time
import random
from bs4 import BeautifulSoup


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
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main Background - Clean Low-Contrast */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Header Styling */
    h1 {
        color: #0f172a;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    
    /* Sidebar - Soft Modern Look */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #0f172a;
    }
    
    /* Input Fields */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        padding: 0.75rem;
    }
    
    .stTextInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"] {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #1d4ed8;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    
    /* Result Card Containers */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    
    /* Hover effect for cards */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }

    /* DataFrame Styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        border-radius: 8px;
        color: #334155;
        font-weight: 500;
    }
    
    /* Tier 1 Badge Styling */
    .tier-badge {
        background-color: #fef2f2;
        color: #dc2626;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid #fecaca;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    
    /* Divider */
    hr {
        margin: 1.5rem 0;
        border-color: #e2e8f0;
    }
    
    /* Metric Value */
    [data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# API FUNCTIONS
# ==========================================

def is_mobile_number(phone):
    """
    Checks if a phone number is likely an Indian mobile number.
    Mobile numbers usually start with 6, 7, 8, 9 (10 digits).
    Landlines usually start with 0 or have STD codes.
    """
    if not phone or phone == "N/A":
        return False
        
    # Remove junk characters
    clean_num = ''.join(filter(str.isdigit, str(phone)))
    
    # Handle Country Code (+91)
    if clean_num.startswith('91') and len(clean_num) > 10:
        clean_num = clean_num[2:]
        
    # Mobile check: 10 digits, starts with 6-9
    if len(clean_num) == 10 and clean_num[0] in ['6', '7', '8', '9']:
        return True
        
    return False

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
    
    for category in categories:
        for page in range(1, 3):
            if len(all_results) >= 50:
                break
                
            url = "https://google.serper.dev/places"
            payload = json.dumps({
                "q": f"{category} in {pincode}",
                "location": f"{pincode}, India",
                "page": page
            })
            
            try:
                response = requests.request("POST", url, headers=headers, data=payload)
                response.raise_for_status()
                data = response.json()
                
                places = data.get("places", [])
                if not places:
                    break
                    
                for place in places:
                    cid = place.get("cid") or place.get("title")
                    phone = place.get("phoneNumber", "N/A")
                    
                    # Filter: Must be Unique ID AND Valid Mobile Number
                    if cid not in seen_ids:
                        if is_mobile_number(phone):
                            seen_ids.add(cid)
                            all_results.append({
                                "Company Name": place.get("title"),
                                "Address": place.get("address"),
                                "Phone Number": phone,
                                "Website": place.get("website", "N/A"),
                                "Rating": place.get("rating", "N/A"),
                                "Type": place.get("type", "N/A"),
                                "Category": category, 
                                "Directors": [], 
                                "Lead Score": 0,
                                "Tier": "Standard" 
                            })
            except Exception as e:
                pass
            
            time.sleep(0.2)
        
        if len(all_results) >= 50:
            break
            
    return all_results[:50]

def is_small_retail_shop(company):
    """Check if company appears to be a small retail shop."""
    # We are now searching for specific High-Pain categories, so filtering is less critical 
    # but still good to remove obvious noise.
    small_shop_keywords = [
        'kirana', 'grocery', 'bakery', 'cafe', 'parlor',
        'stationery', 'gift', 'flower', 'sweet', 'pan shop', 
        'xerox', 'cyber', 'tea', 'coffee', 'wine'
    ]
    
    company_name = company.get('Company Name', '').lower()
    
    for keyword in small_shop_keywords:
        if keyword in company_name:
            return True
            
    return False

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
    """Calculates 0-5 star rating based on data quality."""
    score = 1 # Start with 1
    
    # 1. Website Check
    if company.get('Website') not in ['N/A', '', None]:
        score += 1
        
    # 2. Directors Found
    directors = company.get('Directors', [])
    if directors and len(directors) > 0:
        score += 1
        
    # 3. Employee Count > 50
    emp_count = company.get('Employee Count')
    if emp_count and isinstance(emp_count, int) and emp_count > 50:
        score += 1
        
    # 4. Tier-1 Priority Bonus
    if company.get('Tier') == 'Tier-1 Priority':
        score += 1.5 # Big bonus for high pain indicators
        
    # 5. Has LinkedIn Bonus
    if company.get("Has_LinkedIn"):
        score += 0.5
        
    return min(5, round(score, 1))

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
                
            with st.spinner("🔍 Discovering High-Pain HCM leads (BPOs, Manufacturing, Hospitals, Construction)..."):
                companies = get_50_companies_from_serper(pincode, SERPER_API_KEY)
                
            if not companies:
                st.warning("⚠️ No companies found for this pincode.")
            else:
                # Filter 1: Companies with valid websites (Optional but recommended)
                # Filter 2: Remove small retail shops
                quality_companies = [c for c in companies if not is_small_retail_shop(c)]
                
                st.session_state["discovered_data"] = quality_companies
                st.session_state["pincode"] = pincode
                st.rerun()

    st.markdown("")
    st.divider()
    st.markdown("### ℹ️ How it Works")
    st.markdown("""
    1. **Discovery**: Fetches ~50 High-Pain Leads (BPO, Mfg, Hospital, Construction).
    2. **Selection**: You choose which to enrich.
    3. **Enrichment**: Finds Directors, Employee Count, & "Tier-1" Signals.
    4. **Contact**: Reveal direct mobile numbers.
    """)

# Main Content Area

# State: Landing Page
if "discovered_data" not in st.session_state and "enriched_data" not in st.session_state:
    st.markdown("")
    st.markdown("")
    st.markdown("<h1 style='text-align: center; color: #1e40af;'>Company Discovery Tool 🔍</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Find High-Pain HCM Leads & Decision Makers.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background-color: white; padding: 2rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <h3>� Ready to hunt?</h3>
            <p style="color: #64748b; margin-bottom: 1.5rem;">Enter a pincode in the sidebar to uncover high-quality BPO, Manufacturing, and Healthcare leads.</p>
            <div style="background-color: #f1f5f9; padding: 0.75rem; border-radius: 8px; font-size: 0.9rem; color: #475569;">
                👈 <strong>Start in the Sidebar</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

# State: Discovery Results (Selection Phase)
elif "discovered_data" in st.session_state and "enriched_data" not in st.session_state:
    data = st.session_state["discovered_data"]
    pincode_display = st.session_state.get("pincode", "")
    
    st.markdown(f"### 📋 Discovered High-Pain Leads in {pincode_display}")
    st.info(f"Found {len(data)} potential companies across BPO, Construction, Hospitals, & Mfg. Select to enrich.")
    
    # Create a DataFrame for selection
    df_discovery = pd.DataFrame(data)
    
    # Add a selection column (default True for top 10 to save time/clicks)
    df_discovery.insert(0, "Enrich", False)
    # Default select top 10 valid websites
    for idx in df_discovery.index[:10]:
        df_discovery.at[idx, "Enrich"] = True
        
    # Display editable dataframe
    edited_df = st.data_editor(
        df_discovery,
        column_config={
            "Enrich": st.column_config.CheckboxColumn(
                "Enrich?",
                help="Select to find Directors & Employee Count",
                default=False,
            ),
            "Company Name": st.column_config.TextColumn("Company"),
            "Category": st.column_config.TextColumn("Lead Type"),
            "Website": st.column_config.LinkColumn("Website"),
        },
        disabled=["Company Name", "Address", "Phone Number", "Website", "Rating", "Type", "Category"],
        hide_index=True,
        use_container_width=True
    )
    
    # Button to proceed
    selected_indices = edited_df[edited_df["Enrich"]].index
    num_selected = len(selected_indices)
    
    if st.button(f"✨ Enrich {num_selected} Selected Companies", type="primary"):
        if num_selected == 0:
            st.error("Please select at least one company.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            enriched_companies = []
            
            # Loop through selected companies
            for i, idx in enumerate(selected_indices):
                company = data[idx]
                status_text.text(f"Processing {i+1}/{num_selected}: {company['Company Name']}...")
                
                # 1. Get Employee Count & Validate with Snippet
                emp_count, snippet, linkedin_url = get_employee_count(company['Company Name'], SERPER_API_KEY)
                company["Employee Count"] = emp_count if emp_count else "N/A"
                company["Has_LinkedIn"] = bool(linkedin_url)
                
                # Check for High-Pain signals in snippet
                snippet_lower = snippet.lower()
                if "multiple locations" in snippet_lower or "hiring" in snippet_lower or "night shift" in snippet_lower or "urgently" in snippet_lower:
                    company["Tier"] = "Tier-1 Priority"
                else:
                    company["Tier"] = "Standard"
                
                # 2. Get Directors
                directors = get_zauba_directors(company['Company Name'], SERPER_API_KEY)
                company["Directors"] = directors
                
                # 3. Calculate Score
                company["Lead Score"] = calculate_lead_score(company)
                
                enriched_companies.append(company)
                progress_bar.progress((i + 1) / num_selected)
                
            st.session_state["enriched_data"] = enriched_companies
            st.rerun()

# State: Enriched Results & Contact Reveal
elif "enriched_data" in st.session_state:
    enriched = st.session_state["enriched_data"]
    
    st.markdown("### 💎 Enriched Leads")
    
    if st.button("⬅️ Back to Selection"):
        del st.session_state["enriched_data"]
        st.rerun()
        
    st.divider()
    
    # Custom List View for "Button per Row" requirement
    for company in enriched:
        with st.container():
            # Layout: Title & Tier Badge
            col_header, col_score = st.columns([0.7, 0.3])
            with col_header:
                st.markdown(f"### {company['Company Name']}")
                if company.get("Tier") == "Tier-1 Priority":
                     st.markdown('<span class="tier-badge">🔥 TIER-1 PRIORITY</span>', unsafe_allow_html=True)
            
            with col_score:
                st.markdown(f"<div style='text-align: right'>{'⭐' * int(company['Lead Score'])}</div>", unsafe_allow_html=True)
            
            st.markdown("") # Spacer

            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                st.caption("DETAILS")
                st.write(f"🏢 {company['Address']}")
                st.write(f"🏷️ {company.get('Category', 'N/A')}")
                
            with c2:
                st.caption("METRICS")
                st.write(f"👥 **Employees:** {company.get('Employee Count', 'N/A')}")
                
                links = []
                if company.get("Website") != "N/A":
                    links.append(f"[Website]({company['Website']})")
                if company.get("Has_LinkedIn"):
                    links.append(f"✅ LinkedIn")
                if links:
                    st.markdown(" | ".join(links))
                
            with c3:
                st.caption("DECISION MAKERS")
                directors = company.get("Directors", [])
                if directors:
                    for d in directors:
                        st.write(f"• {d}")
                else:
                    st.write("No directors found")
                            
            # Contact Reveal Section inside the card
            st.markdown("")
            with st.expander("🔍 Find Contact Number"):
                if not directors:
                    st.warning("No director names available to search.")
                else:
                    st.markdown("Select a director to find their contact details:")
                    cols = st.columns(len(directors))
                    for i, director in enumerate(directors):
                        # Use a simpler button layout
                        if st.button(f"Search: {director}", key=f"btn_{company['Company Name']}_{i}"):
                            with st.spinner(f"Searching for {director}..."):
                                results = reveal_director_contact(director, company['Company Name'], SERPER_API_KEY)
                                if results:
                                    for res in results:
                                        st.success(f"**Found:** {res['title']}")
                                        st.caption(res['snippet'])
                                else:
                                    st.error("No direct contact info found.")
            # st.divider() removed for cleaner look
            
    # Export Option
    df_export = pd.DataFrame(enriched)
    # Convert lists to strings for CSV
    df_export["Directors"] = df_export["Directors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Enriched Data CSV",
        data=csv,
        file_name=f'hcm_leads_{int(time.time())}.csv',
        mime='text/csv'
    )


