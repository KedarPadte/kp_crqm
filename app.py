import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 Cyber Risk Quantification Model (CRQM) - Input Wizard")

# ----------- Helper: Normalize -----------
def normalize_company_name(name):
    return name.strip().title()

# ----------- Helper: Revenue Parser -----------
def parse_revenue(text):
    try:
        text = text.lower().replace(",", "")
        if "billion" in text:
            return float(text.replace("$", "").split()[0])
        elif "million" in text:
            return float(text.replace("$", "").split()[0]) / 1000
        elif "crore" in text:
            return float(text.split()[0]) * 0.12  # ₹ Crore to USD Billion approx
        elif "lakh" in text:
            return float(text.split()[0]) * 0.0012
        elif "$" in text:
            return float(text.replace("$", "").split()[0])
    except:
        return None

def parse_employees(text):
    try:
        return int(text.replace(",", "").strip())
    except:
        return None

# ----------- Fetch from CompaniesMarketCap -----------
def get_from_marketcap(company):
    try:
        search_url = f"https://companiesmarketcap.com/search/?query={company.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        link_tag = soup.find('a', class_='link-detail')
        if not link_tag:
            return {}
        
        company_url = "https://companiesmarketcap.com" + link_tag['href']
        page = requests.get(company_url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        data = {}
        rows = soup.find_all("div", class_="company-profile-row")
        for row in rows:
            label = row.find("div", class_="company-profile-row-title").text.strip().lower()
            value = row.find("div", class_="company-profile-row-value").text.strip()
            if "industry" in label: data["industry"] = value
            if "sector" in label: data["sector"] = value
            if "country" in label: data["region"] = value
            if "revenue" in label: data["revenue"] = value
            if "employees" in label: data["employees"] = value
        return data
    except Exception as e:
        return {}

# ----------- Streamlit Inputs -----------
company_input = st.text_input("Enter Company Name", value="American Express")
company_name = normalize_company_name(company_input)

st.markdown(f"🔍 Interpreted as: **{company_name}**")

# ----------- Fetch from fallback chains -----------
marketcap_data = get_from_marketcap(company_name)

# Extract with fallback logic
industry = marketcap_data.get("industry", "Unknown")
sector = marketcap_data.get("sector", "Unknown")
region = marketcap_data.get("region", "Unknown")
revenue_raw = marketcap_data.get("revenue")
employees_raw = marketcap_data.get("employees")

# Parse revenue and employees
revenue_billion = parse_revenue(revenue_raw) if revenue_raw else 1.0
employee_count = parse_employees(employees_raw) if employees_raw else 10000

# ----------- Display UI -----------
st.markdown("### 📊 Company Profile")
st.write(f"🏭 **Industry:** {industry}")
st.write(f"📌 **Sector:** {sector}")
st.write(f"🌎 **Region (estimated):** {region}")

employees = st.number_input("Estimated Number of Employees", min_value=1, value=employee_count)
revenue = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1, value=revenue_billion)

st.success("✅ Company info auto-fetched (with fallback chain) and ready for CRQM modeling.")
