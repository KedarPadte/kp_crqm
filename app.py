import streamlit as st

# ---------- Page Setup ----------
st.set_page_config(page_title="CRQM Input Wizard", layout="wide")
st.title("🔐 CRQM – Company Risk Profiling")

# ---------- 1. Company Info ----------
with st.expander("🏢 Company Info", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", value="American Express")
        region = st.selectbox("Region", ["India", "US", "Europe", "Middle East", "APAC"])
    with col2:
        revenue = st.number_input("Revenue (in Billion USD)", min_value=0.0, step=0.1, value=20.0)
        employees = st.number_input("Employees", min_value=1, value=50000)

    industry = st.text_input("Industry", value="Finance")
    sector = st.text_input("Sector", value="Banking")

company_info = {
    "Name": company_name,
    "Region": region,
    "Revenue (Billion USD)": revenue,
    "Employees": employees,
    "Industry": industry,
    "Sector": sector
}

# ---------- 2. Sensitivity Level Setup ----------
st.markdown("### 🧩 Sensitivity Classification Setup")
sensitivity_levels = st.slider("Number of Sensitivity Levels", min_value=3, max_value=7, value=5)
level_labels = [f"Level {i}" for i in range(1, sensitivity_levels + 1)]

# ---------- 3. Asset Inputs ----------
st.markdown("### 📦 Data Asset Counts")
col1, col2, col3 = st.columns(3)
with col1:
    pii_total = st.number_input("PII Records", min_value=0, value=1_000_000)
with col2:
    ip_total = st.number_input("IP Assets", min_value=0, value=500)
with col3:
    ot_total = st.number_input("OT Assets", min_value=0, value=100)

# ---------- Helper to Get Distribution ----------
def get_distribution(asset_type, total):
    st.markdown(f"**{asset_type} Classification Distribution (%):**")
    cols = st.columns(len(level_labels))
    percentages = []
    for i, col in enumerate(cols):
        with col:
            pct = st.number_input(f"{level_labels[i]}", min_value=0, max_value=100, step=5, key=f"{asset_type}_{i}")
            percentages.append(pct)
    if sum(percentages) != 100:
        st.warning(f"⚠️ {asset_type}: Percentages should sum to 100%.")
    counts = [round((pct / 100) * total) for pct in percentages]
    return dict(zip(level_labels, counts))

# ---------- 4. Classification Distribution ----------
st.markdown("### 🧮 Classification Breakdown")

with st.expander("🔒 PII Classification"):
    pii_dist = get_distribution("PII", pii_total)
with st.expander("💡 IP Classification"):
    ip_dist = get_distribution("IP", ip_total)
with st.expander("⚙️ OT Classification"):
    ot_dist = get_distribution("OT", ot_total)

# ---------- 5. Final Summary ----------
if st.button("✅ Generate CRQM Profile"):
    summary = {
        "Company Info": company_info,
        "Sensitivity Levels": level_labels,
        "Asset Counts": {
            "PII": pii_total,
            "IP": ip_total,
            "OT": ot_total
        },
        "Classified Assets": {
            "PII": pii_dist,
            "IP": ip_dist,
            "OT": ot_dist
        }
    }
    st.success("CRQM Profile Generated Successfully!")
    st.json(summary)
