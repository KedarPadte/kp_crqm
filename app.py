
import streamlit as st
import requests

st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title(" Cyber Risk Quantification Model (CRQM) - Input Wizard")

# ---------- CLEARBIT CONFIG ----------
CLEARBIT_API_KEY = "sk_live_YOUR_API_KEY_HERE"

# ---------- COMPANY NAME NORMALIZATION ----------
def normalize_company_name(input_name):
    query = input_name.lower().strip()
    url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={query}"
    try:
        response = requests.get(url)
        data = response.json()
        if data:
            return data[0]['name'], data[0]['domain']
        else:
            return input_name.title(), None
    except:
        return input_name.title(), None

# ---------- CLEARBIT ENRICHMENT ----------
def get_company_profile(domain):
    headers = {
        "Authorization": f"Bearer {CLEARBIT_API_KEY}"
    }
    url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            revenue = data.get("metrics", {}).get("estimatedAnnualRevenue", None)
            employees = data.get("metrics", {}).get("employees", None)
            industry = data.get("category", {}).get("industry", "Unknown")
            sector = data.get("category", {}).get("sector", "Unknown")
            country = data.get("geo", {}).get("country", "Unknown")
            return revenue, employees, industry, sector, country
        else:
            return None, None, "Unknown", "Unknown", "Unknown"
    except:
        return None, None, "Unknown", "Unknown", "Unknown"

# ---------- INPUTS ----------
raw_input = st.text_input("Enter Company Name", value="American Express")
normalized_name, domain = normalize_company_name(raw_input)

st.write(f"🔍 Interpreted as: **{normalized_name}**")
if domain:
    st.markdown(f"**Website:** [https://{domain}](https://{domain})")

# Auto-fetch additional company info
revenue, employees_auto, industry, sector, region_auto = None, None, "Unknown", "Unknown", "Unknown"
if domain:
    revenue, employees_auto, industry, sector, region_auto = get_company_profile(domain)

# Show retrieved info and allow edits
st.markdown("### Company Profile")
st.write(f"**Industry:** {industry}")
st.write(f"**Sector:** {sector}")
st.write(f"**Region (auto-detected):** {region_auto}")

employees = st.number_input("Estimated Number of Employees", min_value=1, value=employees_auto or 1000)
revenue_billion = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1,
                                  value=(revenue / 1_000_000_000) if isinstance(revenue, (int, float)) else 1.0)

# Continue from here with the rest of the form as needed
st.success("Company info fetched and ready for CRQM modeling.")
