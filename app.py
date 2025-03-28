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
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, 'html.parser')
        link_tag = soup.find('a', class_='link-detail')

        if not link_tag:
            return None, None, None, None, None

        company_url = "https://companiesmarketcap.com" + link_tag['href']
        company_response = requests.get(company_url, headers=headers, timeout=10)
        company_soup = BeautifulSoup(company_response.text, 'html.parser')

        # Region/Country
        country_span = company_soup.find('span', string="Country")
        country = country_span.find_next('div').text.strip() if country_span else "Unknown"

        # Sector
        category_tags = company_soup.find_all('a', class_='company-category')
        sector = ", ".join([tag.text.strip() for tag in category_tags]) if category_tags else "Unknown"

        # Revenue (try to find where "Revenue" is mentioned in tabs or sections)
        revenue_section = company_soup.find('a', string="Revenue")
        revenue = "N/A"
        if revenue_section:
            parent_section = revenue_section.find_parent('li')
            if parent_section:
                revenue_div = parent_section.find_next('div', class_='subsection')
                if revenue_div:
                    text = revenue_div.get_text()
                    for line in text.splitlines():
                        if "$" in line and ("billion" in line.lower() or "million" in line.lower()):
                            revenue = line.strip()
                            break

        # Sector/Industry from header if available
        overview = company_soup.find('div', class_='company-description')
        industry = "Unknown"
        if overview:
            if "provider of" in overview.text.lower():
                industry = overview.text.split("provider of")[-1].split(".")[0].strip().capitalize()

        return revenue, None, industry, sector, country

    except Exception as e:
        return None, None, None, None, None

# --------- Normalize Company Name ---------
def normalize_company_name(input_name):
    return input_name.strip().title()

# --------- INPUT ---------
raw_input = st.text_input("Enter Company Name", value="American Express")
normalized_name = normalize_company_name(raw_input)
st.write(f"🔍 Interpreted as: **{normalized_name}**")

# --------- SCRAPE DATA ---------
revenue_str, employees_auto, industry, sector, region_auto = get_company_data_from_marketcap(normalized_name)

# Revenue formatting
def parse_revenue(rev_text):
    try:
        if "billion" in rev_text.lower():
            return float(rev_text.replace("$", "").split()[0])
        elif "million" in rev_text.lower():
            return float(rev_text.replace("$", "").split()[0]) / 1000
    except:
        return 1.0  # fallback

revenue_billion = parse_revenue(revenue_str or "1.0")

# --------- DISPLAY ---------
st.markdown("### 📊 Company Profile")
st.write(f"🏭 **Industry:** {industry or 'Unknown'}")
st.write(f"📌 **Sector:** {sector or 'Unknown'}")
st.write(f"🌎 **Region (estimated):** {region_auto or 'Unknown'}")

employees = st.number_input("Estimated Number of Employees", min_value=1, value=employees_auto or 1000)
revenue_input = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1, value=revenue_billion)

st.success("✅ Company info auto-fetched and ready for CRQM modeling.")
