import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 Cyber Risk Quantification Model (CRQM) - Input Wizard")

# --------- Helper: Scrape CompaniesMarketCap ---------
def get_company_data_from_marketcap(company_name):
    search_url = f"https://companiesmarketcap.com/search/?query={company_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        search_response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(search_response.text, 'html.parser')
        link_tag = soup.find('a', class_='link-detail')

        if not link_tag:
            return None, None, None, None, None

        company_url = "https://companiesmarketcap.com" + link_tag['href']
        company_response = requests.get(company_url, headers=headers)
        company_soup = BeautifulSoup(company_response.text, 'html.parser')

        # Revenue
        revenue_div = company_soup.find('div', text=lambda x: x and 'Revenue' in x)
        revenue = revenue_div.find_next('div').text.strip() if revenue_div else 'N/A'

        # Sector
        sector_div = company_soup.find('div', text=lambda x: x and 'Sector' in x)
        sector = sector_div.find_next('div').text.strip() if sector_div else 'N/A'

        # Industry
        industry_div = company_soup.find('div', text=lambda x: x and 'Industry' in x)
        industry = industry_div.find_next('div').text.strip() if industry_div else 'N/A'

        # Country
        country_div = company_soup.find('div', text=lambda x: x and 'Country' in x)
        country = country_div.find_next('div').text.strip() if country_div else 'N/A'

        return revenue, None, industry, sector, country

    except Exception as e:
        return None, None, None, None, None

# --------- Normalize Company Name ---------
def normalize_company_name(input_name):
    return input_name.strip().title()

# --------- INPUTS ---------
raw_input = st.text_input("Enter Company Name", value="American Express")
normalized_name = normalize_company_name(raw_input)

st.write(f"🔍 Interpreted as: **{normalized_name}**")

# Fetch public info from CompaniesMarketCap
revenue_str, employees_auto, industry, sector, region_auto = get_company_data_from_marketcap(normalized_name)

# Revenue formatting
def parse_revenue(rev_text):
    try:
        if "billion" in rev_text.lower():
            return float(rev_text.replace("$", "").split()[0])
        elif "million" in rev_text.lower():
            return float(rev_text.replace("$", "").split()[0]) / 1000
    except:
        return 1.0  # default fallback

revenue_billion = parse_revenue(revenue_str or "1.0")

# --------- DISPLAY ---------
st.markdown("### 📊 Company Profile")
st.write(f"🏭 **Industry:** {industry or 'Unknown'}")
st.write(f"📌 **Sector:** {sector or 'Unknown'}")
st.write(f"🌎 **Region (estimated):** {region_auto or 'Unknown'}")

employees = st.number_input("Estimated Number of Employees", min_value=1, value=employees_auto or 1000)
revenue_input = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1, value=revenue_billion)

st.success("Company info auto-fetched and ready for CRQM modeling.")
