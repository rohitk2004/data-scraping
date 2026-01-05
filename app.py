import streamlit as st
import pandas as pd
import requests
import json
import time

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
SERPER_API_KEY = "742d04fef1125feb19ad7b6123f3e8852d0fee4f"

# ==========================================
# CUSTOM CSS - BLUE & WHITE PROFESSIONAL THEME
# ==========================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%);
        color: #1f2937;
    }
    
    /* Force text color for headers and paragraphs in main area */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp p, .stApp li, .stApp span {
        color: #1f2937;
    }
    
    /* Header Styling */
    h1 {
        color: #1e40af;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-align: center;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Subtitle */
    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stTextInput input {
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #1f2937 !important;
        border-radius: 8px;
        padding: 0.75rem;
    }
    
    [data-testid="stSidebar"] .stTextInput input::placeholder {
        color: rgba(31, 41, 55, 0.5) !important;
    }
    
    /* Button Styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    
    /* DataFrame Styling */
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #1e40af;
        font-weight: 700;
    }
    
    /* Info Box */
    .info-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #3b82f6;
        margin-bottom: 1.5rem;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #cbd5e1 50%, transparent 100%);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# API FUNCTIONS
# ==========================================

def search_places_serper(pincode, api_key):
    """Searches for larger entities using targeted keywords."""
    url = "https://google.serper.dev/places"
    
    # Targeted keywords to find larger businesses
    search_terms = [
        f"Corporate Office {pincode}",
        f"Manufacturing {pincode}",
        f"Logistics {pincode}",
        f"Tech Park {pincode}"
    ]
    
    all_results = []
    seen_names = set()
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    for term in search_terms:
        payload = json.dumps({
            "q": term,
            "gl": "in"
        })
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            
            places = data.get("places", [])
            
            for place in places:
                company_name = place.get("title")
                # Avoid duplicates
                if company_name and company_name not in seen_names:
                    seen_names.add(company_name)
                    all_results.append({
                        "Company Name": company_name,
                        "Address": place.get("address"),
                        "Phone Number": place.get("phoneNumber", "N/A"),
                        "Website": place.get("website", "N/A"),
                        "Rating": place.get("rating", "N/A"),
                        "Reviews": place.get("ratingCount", "N/A"),
                        "Type": place.get("type", "N/A")
                    })
            
            time.sleep(0.5)  # Small delay between searches
            
        except Exception as e:
            continue
    
    if not all_results:
        st.error(f"❌ No companies found for targeted search.")
    
    return all_results

def is_small_retail_shop(company):
    """Check if company appears to be a small retail shop to avoid wasting API credits."""
    small_shop_keywords = [
        'shop', 'store', 'retail', 'boutique', 'mart', 'kirana', 
        'grocery', 'bakery', 'cafe', 'restaurant', 'salon', 'parlor',
        'medical store', 'pharmacy', 'stationery', 'gift shop',
        'flower shop', 'sweet shop', 'general store', 'pan shop'
    ]
    
    small_shop_types = [
        'clothing_store', 'convenience_store', 'grocery_or_supermarket',
        'restaurant', 'cafe', 'bakery', 'meal_takeaway', 'food',
        'shopping', 'store', 'supermarket'
    ]
    
    company_name = company.get('Company Name', '').lower()
    company_type = company.get('Type', 'N/A')
    
    # Check if name contains small shop keywords
    for keyword in small_shop_keywords:
        if keyword in company_name:
            return True
    
    # Check business type if available
    if company_type != 'N/A':
        for shop_type in small_shop_types:
            if shop_type in company_type.lower():
                return True
    
    return False

def get_employee_count(company_name, api_key):
    """Searches Google for LinkedIn employee count."""
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
            return None
            
        snippet = organic[0].get("snippet", "")
        title = organic[0].get("title", "")
        full_text = snippet + " " + title
        
        import re
        
        # Extract employee count
        emp_count = None
        match = re.search(r"([\d,]+)(?:\+|-\d+)?\s+employees", full_text, re.IGNORECASE)
        if match:
            count_str = match.group(1).replace(',', '')
            try:
                emp_count = int(count_str)
            except ValueError:
                emp_count = None
        
        return emp_count
        
    except Exception as e:
        return None

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
        submit_button = st.form_submit_button("🚀 Start Search", type="primary")

    if submit_button:
        if not pincode:
            st.error("⚠️ Please enter a Pincode.")
        else:
            with st.spinner("🔍 Searching for companies..."):
                companies = search_places_serper(pincode, SERPER_API_KEY)
                
            if not companies:
                st.warning("⚠️ No companies found for this pincode.")
            else:
                # Filter 1: Companies with valid websites
                companies_with_website = [c for c in companies if c.get('Website') != 'N/A']
                
                # Filter 2: Remove small retail shops to save credits
                quality_companies = [c for c in companies_with_website if not is_small_retail_shop(c)]
                
                st.info(f"✅ Found {len(companies)} companies. Analyzing {len(quality_companies)} medium-to-large businesses...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                enriched_data = []
                skipped_count = 0
                
                for i, company in enumerate(quality_companies):
                    status_text.text(f"📊 Analyzing: {company['Company Name'][:30]}...")
                    
                    emp_count = get_employee_count(company['Company Name'], SERPER_API_KEY)
                    
                    # Only add to results if employee count >= 80
                    if emp_count is not None and emp_count >= 80:
                        company["Employee Count"] = emp_count
                        enriched_data.append(company)
                    else:
                        skipped_count += 1
                    
                    progress_bar.progress((i + 1) / len(quality_companies))
                    time.sleep(0.1)
                
                if enriched_data:
                    df_results = pd.DataFrame(enriched_data)
                    # Reorder columns for better visibility
                    column_order = [
                        "Company Name", "Type", "Employee Count", 
                        "Website", "Phone Number", "Address", 
                        "Rating", "Reviews"
                    ]
                    # Filter for columns that actually exist in the data
                    final_cols = [col for col in column_order if col in df_results.columns]
                    st.session_state["serper_data"] = df_results[final_cols]
                    st.session_state["pincode"] = pincode
                    st.session_state["skipped_count"] = skipped_count
                else:
                    st.warning("⚠️ No companies found with 80+ employees.")
                status_text.text("✨ Analysis complete!")
                time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
    
    st.markdown("")
    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    This tool helps you discover companies in any location using just a pincode.
    
    **Features:**
    - 📍 Location-based search
    - 📊 LinkedIn employee data
    - 📞 Contact information
    - 💾 Export to CSV
    """)

# Main Content Area
if "serper_data" in st.session_state:
    df = st.session_state["serper_data"]
    pincode_display = st.session_state.get("pincode", "")
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Companies", len(df))
    
    with col2:
        with_phone = df[df["Phone Number"] != "N/A"].shape[0]
        st.metric("📞 With Phone", with_phone)
    
    with col3:
        with_website = df[df["Website"] != "N/A"].shape[0]
        st.metric("🌐 With Website", with_website)
    
    with col4:
        with_employees = df[df["Employee Count"] != "Not Found"].shape[0]
        st.metric("👥 With Employee Data", with_employees)
    
    st.divider()
    
    # Results Section
    st.markdown(f"### 📋 Results for Pincode: **{pincode_display}**")
    st.markdown("")
    
    # Display DataFrame
    st.dataframe(
        df,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Download Section
    st.markdown("")
    col_download1, col_download2, col_download3 = st.columns([2, 1, 2])
    

    with col_download2:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f'companies_{pincode_display}_{int(time.time())}.csv',
            mime='text/csv',
            use_container_width=True
        )

else:
    # Empty State / Landing Page
    st.markdown("")
    st.markdown("")
    st.markdown("")
    
    st.markdown("<h1 style='text-align: center; color: #1e40af;'>Company Discovery Tool 🔍</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Find businesses and get contact details in seconds.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👈 **Start via the Sidebar**\n\n1.  **Enter a Pincode** (e.g., 560001)\n2.  Click **Start Search**\n3.  Get enriched data instantly!")
    
    # Optional: Add some visual elements or features preview
    st.markdown("")
    st.markdown("---")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.markdown("### 📍 **Smart Search**")
        st.write("Targeted search combining Maps & Search APIs to find real businesses, not just listings.")

    with col_f2:
        st.markdown("### 👥 **Employee Data**")
        st.write("Enrich results with LinkedIn employee counts to identify established growing companies.")

    with col_f3:
        st.markdown("### ⚡ **Data Export**")
        st.write("Export your findings directly to CSV for your sales or marketing pipelines.")

