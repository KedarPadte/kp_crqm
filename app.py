
import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import wikipedia

# --------------------- CONFIG ---------------------
st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 Cyber Risk Quantification Model (CRQM) - Input Wizard")

# ----------------- Gemini API Setup -----------------
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
def gemini_enrich_company(company_name):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    prompt = f"Normalize this company name and give its official name, revenue in billions USD, employee count, domain/sector, industry, and region/country. Return JSON. Company: {company_name}"
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        r = requests.post(url, headers=headers, params=params, json=data)
        response_text = r.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(response_text)
    except:
        return {}

# ----------------- CompaniesMarketCap Scraper -----------------
def get_data_from_companiesmarketcap(company_name):
    try:
        search_url = f"https://companiesmarketcap.com/search/?query={company_name.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        search_response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(search_response.text, 'html.parser')
        link_tag = soup.find('a', class_='link-detail')
        if not link_tag:
            return {}
        company_url = "https://companiesmarketcap.com" + link_tag['href']
        company_response = requests.get(company_url, headers=headers)
        soup = BeautifulSoup(company_response.text, 'html.parser')
        data = {
            "revenue": soup.find("div", string=lambda x: x and "Revenue" in x).find_next("div").text.strip() if soup.find("div", string=lambda x: x and "Revenue" in x) else None,
            "industry": soup.find("div", string=lambda x: x and "Industry" in x).find_next("div").text.strip() if soup.find("div", string=lambda x: x and "Industry" in x) else None,
            "sector": soup.find("div", string=lambda x: x and "Sector" in x).find_next("div").text.strip() if soup.find("div", string=lambda x: x and "Sector" in x) else None,
            "region": soup.find("div", string=lambda x: x and "Country" in x).find_next("div").text.strip() if soup.find("div", string=lambda x: x and "Country" in x) else None
        }
        return data
    except:
        return {}

# ----------------- Wikipedia Fallback -----------------
def get_data_from_wikipedia(company_name):
    try:
        summary = wikipedia.summary(company_name, sentences=2)
        return {"industry": "Check summary", "sector": "General", "region": "Global", "summary": summary}
    except:
        return {}

# ----------------- Full Fallback Chain -----------------
def fetch_company_metadata(company_name):
    # 1. Try Gemini
    gemini_data = gemini_enrich_company(company_name)
    if gemini_data:
        return gemini_data

    # 2. Try CompaniesMarketCap
    marketcap_data = get_data_from_companiesmarketcap(company_name)
    if any(marketcap_data.values()):
        return marketcap_data

    # 3. TODO: Crunchbase, Clearbit, MoneyControl, Screener
    # [Placeholders here for later]

    # 4. Wikipedia Fallback
    return get_data_from_wikipedia(company_name)

# ----------------- Streamlit UI -----------------
company_input = st.text_input("Enter Company Name", value="American Express")
st.write(f"🔍 Interpreted as: **{company_input.title()}**")

metadata = fetch_company_metadata(company_input)

# Format revenue
def parse_revenue(rev_text):
    try:
        if "billion" in rev_text.lower():
            return float(rev_text.replace("$", "").split()[0])
        elif "million" in rev_text.lower():
            return float(rev_text.replace("$", "").split()[0]) / 1000
    except:
        return 1.0
revenue_val = parse_revenue(metadata.get("revenue", "1.0")) if "revenue" in metadata else 1.0

# UI Display
st.markdown("### 📊 Company Profile")
st.write(f"🏭 **Industry:** {metadata.get('industry', 'Unknown')}")
st.write(f"📌 **Sector:** {metadata.get('sector', 'Unknown')}")
st.write(f"🌍 **Region:** {metadata.get('region', 'Unknown')}")

employees = st.number_input("Estimated Number of Employees", min_value=1, value=int(metadata.get("employees", 10000)))
revenue = st.number_input("Estimated Revenue (in billions USD)", min_value=0.1, value=revenue_val)

st.success("✅ Company info auto-fetched (with fallback chain) and ready for CRQM modeling.")
