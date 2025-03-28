import streamlit as st

st.set_page_config(page_title="CRQM Asset Classification", layout="wide")
st.title("🔐 CRQM – Sensitivity-Based Asset Classification")

# --- STEP 1: Number of Classification Levels ---
st.header("📊 Set Classification Levels")
num_levels = st.selectbox("Select number of data sensitivity levels", [3, 4, 5, 6, 7], index=2)
classification_labels = [f"Level {i+1}" for i in range(num_levels)]

# --- STEP 2: Raw Asset Inputs ---
st.header("📦 Asset Inventory")
col1, col2, col3 = st.columns(3)
with col1:
    pii = st.number_input("📁 PII Records (millions)", min_value=0.0, step=0.1, value=1.0)
    phi = st.number_input("📁 PHI Records (millions)", min_value=0.0, step=0.1, value=0.0)
    pci = st.number_input("📁 PCI Records (millions)", min_value=0.0, step=0.1, value=0.0)
with col2:
    ip_assets = st.number_input("💡 IP Assets (count)", min_value=0, step=1, value=100)
with col3:
    ot_assets = st.number_input("⚙️ OT Systems (count)", min_value=0, step=1, value=20)

# --- STEP 3: Classification Distribution ---
st.header("📌 Sensitivity Classification (%)")

def get_classification_distribution(asset_name):
    st.subheader(f"🔐 {asset_name} Classification Distribution")
    distribution = {}
    total = 0
    for level in classification_labels:
        val = st.number_input(f"{asset_name} → {level}", min_value=0, max_value=100, step=5, value=0,
                              key=f"{asset_name}_{level}")
        distribution[level] = val
        total += val
    if total != 100:
        st.warning(f"⚠️ {asset_name} classification must sum to 100% (currently {total}%)")
    return distribution

pii_dist = get_classification_distribution("PII")
ip_dist = get_classification_distribution("IP")
ot_dist = get_classification_distribution("OT")

# --- STEP 4: Auto-calculate actual assets per level ---
def calc_distribution(base_count, distribution_dict, scale=1):
    return {level: round((pct / 100) * base_count * scale, 2) for level, pct in distribution_dict.items()}

if st.button("✅ Generate Sensitivity Distribution Report"):
    st.success("🔍 Distribution Generated Based on Inputs")

    st.subheader("📋 Asset Count per Classification Level")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔐 PII Records**")
        pii_counts = calc_distribution(pii, pii_dist, scale=1_000_000)
        st.json(pii_counts)

    with col2:
        st.markdown("**💡 IP Assets**")
        ip_counts = calc_distribution(ip_assets, ip_dist)
        st.json(ip_counts)

    with col3:
        st.markdown("**⚙️ OT Systems**")
        ot_counts = calc_distribution(ot_assets, ot_dist)
        st.json(ot_counts)
