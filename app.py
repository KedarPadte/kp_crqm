import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 Cyber Risk Quantification Model (CRQM) - Input Wizard")

# ---------------- Normalize Name ----------------
def normalize_company_name(name):
    return name.strip().title()

# ---------------- Revenue Parser ----------------
def parse_revenue(text):
    try:
        text = text.lower().replace(",", "")
        if "billion" in text:
            return float(text.replace("$", "").split()[0])
        elif "million" in text:
            return float(text.replace("$", "").split()[0]) / 1000
        elif "crore" in text:
            return float(text.split()[0]) * 0.12  # INR Crore → USD Billion approx
    except:
        return None

# ---------------- CompaniesMarketCap Scraper ----------------
def get_marketcap_data(company):
    search_url = f"https://companiesmarketcap.com/search/?query={company.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        tag = soup.find('a', class_='link-detail')
        if not tag:
            return {}
        url = "https://companiesmarketcap.com" + tag['href']
        r2 = requests.get(url, headers=headers, timeout=10)
        soup2 = BeautifulSoup(r2.text, "html.parser")

        def extract(label):
            div = soup2.find("div", string=lambda x: x and label in x)
            return div.find_next("div").text.strip() if div else None

        return {
            "revenue": extract("Revenue"),
            "industry": extract("Industry"),
            "sector": extract("Sector"),
            "region": extract("Country")
        }
    except:
        return {}

# ---------------- Screener.in Fallback ----------------
def get_screener_data(company):
    try:
        url = f"https://www.screener.in/company/{company.upper()}/"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        info = {}

        facts = soup.select(".company-info .row .col span")
        for idx, span in enumerate(facts):
            txt = span.text.strip().lower()
            if "employees" in txt:
                info["employees"] = int(span.find_next("span").text.replace(",", "").strip())
            elif "industry" in txt:
                info["sector"] = span.find_next("span").text.strip()

        return info
    except:
        return {}

# ---------------- Moneycontrol Fallback ----------------
def get_moneycontrol_data(company):
    try:
        url = f"https://www.moneycontrol.com/stocks/company_info/print_main.php?sc_id={company.upper()}"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select("table b")

        info = {}
        for row in rows:
            text = row.text.strip().lower()
            if "employees" in text:
                val = row.find_next("td").text.strip().replace(",", "")
                info["employees"] = int(val) if val.isnumeric() else None
            elif "industry" in text:
                info["sector"] = row.find_next("td").text.strip()
        return info
    except:
        return {}

# ---------------- INPUT ----------------
company_input = st.text_input("Enter Company Name", value="SBI")
company_name = normalize_company_name(company_input)
st.write(f"🔍 Interpreted as: **{company_name}**")

# ---------------- Fetch Tiered Data ----------------
marketcap_data = get_marketcap_data(company_name)
screener_data = get_screener_data(company_name)
moneycontrol_data = get_moneycontrol_data(company_name)

# ---------------- Fallback Chain ----------------
industry = marketcap_data.get("industry") or screener_data.get("sector") or moneycontrol_data.get("sector") or "Finance"
sector = marketcap_data.get("sector") or screener_data.get("sector") or moneycontrol_data.get("sector") or "Banking"
region = marketcap_data.get("region") or "India"
revenue_text = marketcap_data.get("revenue") or "1 Billion"
employees_val = screener_data.get("employees") or moneycontrol_data.get("employees") or 10000

revenue_billion = parse_revenue(revenue_text) or 1.0

# ---------------- UI ----------------
st.markdown("### 📊 Company Profile")
st.write(f"🏭 **Industry:** {industry}")
st.write(f"📌 **Sector:** {sector}")
st.write(f"🌎 **Region (estimated):** {region}")

employees = st.number_input("Estimated Number of Employees", min_value=1, value=employees_val)
revenue_input = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1, value=revenue_billion)

st.success("✅ Company info auto-fetched (with fallback chain) and ready for CRQM modeling.")
