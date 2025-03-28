
import streamlit as st
import requests

st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 Cyber Risk Quantification Model (CRQM) - Input Wizard")

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
            return revenue, employees
        else:
            return None, None
    except:
        return None, None

# ---------- INPUTS ----------
raw_input = st.text_input("Enter Company Name", value="American Express")
normalized_name, domain = normalize_company_name(raw_input)

st.write(f"🔍 Interpreted as: **{normalized_name}**")
if domain:
    st.write(f"🌐 Company Domain: `{domain}`")

# Auto-fetch revenue and employees if domain is known
estimated_revenue, estimated_employees = None, None
if domain:
    estimated_revenue, estimated_employees = get_company_profile(domain)

# Display + allow manual override
st.markdown("### 📊 Revenue & Workforce")
employees = st.number_input("Estimated Number of Employees", min_value=1, value=estimated_employees or 1000)
revenue = st.number_input("Estimated Revenue (in billions USD)", min_value=0.0, step=0.1,
                          value=(estimated_revenue / 1_000_000_000) if isinstance(estimated_revenue, (int, float)) else 1.0)

# ---------- DOMAIN SELECTION ----------
domains_selected = st.multiselect("Select Business Domains", [
    "Banking", "Insurance", "Retail", "Manufacturing", 
    "Healthcare", "Telecom", "Technology", "Media", "Oil & Gas"
], default=["Banking"])

# ---------- DOMAIN BRANCHING ----------
if "Banking" in domains_selected:
    st.markdown("💳 **Banking-specific fields**")
    st.checkbox("✔ Core Banking System in place?")
    st.checkbox("✔ PCI-DSS Compliant?")

if "Manufacturing" in domains_selected:
    st.markdown("🏭 **Manufacturing-specific fields**")
    st.number_input("No. of OT Systems (e.g., PLCs, SCADA)", min_value=0, value=10)

if "Healthcare" in domains_selected:
    st.markdown("🩺 **Healthcare-specific fields**")
    st.number_input("PHI Records (in millions)", 0.0, step=0.1)

# ---------- CLASSIFICATION ----------
st.markdown("### 🗂️ Data Classification")
classification_labels = [f"Level {i}" for i in range(1, 6)]
classification_distribution = {}
total_percent = 0
for level in classification_labels:
    val = st.number_input(f"% of data at {level}", min_value=0, max_value=100, value=0, step=5)
    classification_distribution[level] = val
    total_percent += val

if total_percent != 100:
    st.warning("⚠️ Total classification percentage should sum to 100%.")

# ---------- PRIVACY DATA ----------
st.markdown("### 🔒 Privacy Data")
pii = st.number_input("PII Records (in millions)", min_value=0.0, step=0.1)
phi = st.number_input("PHI Records (in millions)", min_value=0.0, step=0.1)
pci = st.number_input("PCI Records (in millions)", min_value=0.0, step=0.1)

# ---------- IP ----------
st.markdown("### 💡 Intellectual Property")
ip_assets = st.number_input("Number of IP Assets", min_value=0, value=10)

# ---------- REGION ----------
region = st.selectbox("Operating Region", ["India", "Europe", "US", "Middle East", "APAC"])

# ---------- COMPLIANCE ----------
st.markdown("### 🛡️ Applicable Compliances")
compliance_map = {
    "India": ["DPDA", "RBI Guidelines"],
    "Europe": ["GDPR"],
    "US": ["CCPA", "GLBA"],
    "Middle East": ["PDPL", "NESA"],
    "APAC": ["PDPA", "APRA CPS"]
}
compliances = st.multiselect("Select applicable regulations", options=compliance_map.get(region, []))

# ---------- CONFIRM ----------
if st.button("✅ Confirm Inputs"):
    st.success("Inputs recorded successfully!")
    st.json({
        "Company": normalized_name,
        "Domain": domains_selected,
        "Region": region,
        "Employees": employees,
        "Revenue (Billion USD)": revenue,
        "Classification %": classification_distribution,
        "Privacy Data": {"PII": pii, "PHI": phi, "PCI": pci},
        "IP Assets": ip_assets,
        "Compliances": compliances
    })
