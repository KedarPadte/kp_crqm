import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 Cyber Risk Quantification Model (CRQM) - Input Wizard")


# ---------- Helper: Scrape CompaniesMarketCap ----------
def get_company_data_from_marketcap(company_name):
    try:
        search_url = f"https://companiesmarketcap.com/search/?query={company_name.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, 'html.parser')
        link_tag = soup.find('a', class_='link-detail')
        if not link_tag:
            return None
        company_url = "https://companiesmarketcap.com" + link_tag['href']
        company_response = requests.get(company_url, headers=headers, timeout=10)
        company_soup = BeautifulSoup(company_response.text, 'html.parser')

        def extract_field(label):
            tag = company_soup.find('div', string=lambda x: x and label.lower() in x.lower())
            return tag.find_next('div').text.strip() if tag else None

        return {
            'revenue': extract_field('Revenue'),
            'industry': extract_field('Industry'),
            'sector': extract_field('Sector'),
            'region': extract_field('Country'),
            'employees': None
        }

    except Exception:
        return None


# ---------- Helper: Scrape Screener (Indian companies) ----------
def get_company_data_from_screener(company_name):
    try:
        url = f"https://www.screener.in/company/{company_name.upper()}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rev_tag = soup.find('li', string=lambda x: x and 'Revenue' in x)
        revenue = rev_tag.text.split(":")[-1].strip() if rev_tag else None

        return {
            'revenue': revenue,
            'industry': None,
            'sector': None,
            'region': 'India',
            'employees': None
        }
    except Exception:
        return None


# ---------- Main Fallback Chain ----------
def get_fallback_metadata(company_name):
    data = get_company_data_from_marketcap(company_name)
    if data and any(data.values()):
        return data | {'source': 'CompaniesMarketCap'}

    data = get_company_data_from_screener(company_name)
    if data and any(data.values()):
        return data | {'source': 'Screener'}

    return {
        'revenue': '1.0',
        'industry': 'Finance',
        'sector': 'Banking',
        'region': 'India',
        'employees': '10000',
        'source': 'Fallback Defaults'
    }


# ---------- Revenue Parser ----------
def parse_revenue(rev_text):
    try:
        rev_text = rev_text.lower().replace('$', '').replace(',', '')
        if "billion" in rev_text:
            return float(rev_text.split()[0])
        elif "million" in rev_text:
            return float(rev_text.split()[0]) / 1000
        elif rev_text.replace('.', '', 1).isdigit():
            return float(rev_text)
    except:
        return 1.0
    return 1.0


# ---------- INPUT SECTION ----------
company_input = st.text_input("Enter Company Name", value="American Express")
normalized_name = company_input.strip().title()
st.write(f"🔍 Interpreted as: **{normalized_name}**")

# ---------- Metadata Fetch ----------
metadata = get_fallback_metadata(normalized_name)

industry = metadata.get("industry", "Unknown")
sector = metadata.get("sector", "Unknown")
region = metadata.get("region", "Unknown")
source = metadata.get("source", "None")
rev_val = parse_revenue(metadata.get("revenue", "1.0"))
employees = int(metadata.get("employees") or 10000)

# ---------- DISPLAY ----------
st.markdown("### 📊 Company Profile")
st.write(f"🏭 **Industry:** {industry or 'Unknown'}")
st.write(f"📌 **Sector:** {sector or 'Unknown'}")
st.write(f"🌎 **Region (estimated):** {region or 'Unknown'}")

employees_input = st.number_input("Estimated Number of Employees", min_value=1, value=employees)
revenue_input = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1, value=rev_val)

st.success(f"✅ Company info auto-fetched (via {source}) and ready for CRQM modeling.")
