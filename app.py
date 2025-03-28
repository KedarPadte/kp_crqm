import os
import streamlit as st
import yfinance as yf
import google.generativeai as genai

# === Set Gemini API Key ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("🚨 Gemini API key not found. Please set GEMINI_API_KEY as a secret/environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# === Format revenue nicely ===
def format_revenue(value):
    try:
        value = float(value)
        if value >= 1e12:
            return f"${value / 1e12:.2f} Trillion"
        elif value >= 1e9:
            return f"${value / 1e9:.2f} Billion"
        elif value >= 1e6:
            return f"${value / 1e6:.2f} Million"
        else:
            return f"${value:,.0f}"
    except:
        return value

# === Gemini Ticker Resolver ===
def get_valid_ticker_from_gemini(company_name):
    prompt_check_listing = f"""
    Is the company "{company_name}" publicly listed on any stock exchange?
    If yes, return ONLY its stock ticker (e.g., RELIANCE.NS or AAPL).
    If not, just return: NOT_LISTED
    """
    try:
        response = model.generate_content(prompt_check_listing)
        ticker = response.text.strip()
        if "NOT_LISTED" in ticker.upper():
            followup_prompt = f"""
            List all publicly listed subsidiaries or companies under "{company_name}".
            Return clean numbered list in this format (no comments or notes):
            1. TICKER - Company Name
            2. TICKER - Company Name
            """
            followup = model.generate_content(followup_prompt)
            lines = followup.text.strip().split('\n')
            options = []
            for line in lines:
                parts = line.split(' - ')
                if len(parts) == 2 and '.' in parts[0]:
                    ticker_candidate = parts[0].split('. ', 1)[-1].strip()
                    name = parts[1].strip()
                    if " " not in ticker_candidate:
                        options.append((ticker_candidate, name))
            return None, None, options if options else None
        else:
            return ticker.strip(), company_name.strip(), None
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return None, None, None

# === Yahoo Finance Info Fetch ===
def fetch_company_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Ticker": ticker,
            "Name": info.get("longName", "Not found"),
            "Revenue": info.get("totalRevenue", None),
            "Employees": info.get("fullTimeEmployees", None),
            "Industry": info.get("industry", "Not found"),
            "Sector": info.get("sector", "Not found"),
            "Region": info.get("country", "Not found")
        }
    except Exception as e:
        return {"Error": str(e)}

# === Streamlit App ===
st.set_page_config(page_title="CRQM - Company Enrichment", layout="centered")
st.title("🔐 CRQM - Company Profile Input")

company_input = st.text_input("Enter Company Name", value="Aditya Birla")

if st.button("🔍 Fetch Company Info"):
    with st.spinner("Fetching ticker using Gemini..."):
        ticker, resolved_name, subsidiaries = get_valid_ticker_from_gemini(company_input)

    if subsidiaries:
        choice = st.selectbox("🧭 Select a listed subsidiary", [f"{t} - {n}" for t, n in subsidiaries])
        ticker = choice.split(" - ")[0]
        resolved_name = choice.split(" - ")[1]

    if ticker:
        st.success(f"✅ Ticker Resolved: `{ticker}`  \n📌 Company: **{resolved_name}**")

        company_data = fetch_company_info(ticker)
        if "Error" in company_data:
            st.error(company_data["Error"])
            st.stop()

        # Manual overrides
        st.markdown("### 📊 Auto-Fetched (Editable) Company Info")
        st.text(f"Industry: {company_data.get('Industry')}")
        st.text(f"Sector: {company_data.get('Sector')}")
        st.text(f"Region: {company_data.get('Region')}")

        employees = st.number_input(
            "👥 Estimated Number of Employees",
            min_value=0,
            value=company_data.get("Employees") or 1000
        )

        revenue = st.number_input(
            "💰 Estimated Revenue (in Billions USD)",
            min_value=0.0,
            value=(company_data.get("Revenue") or 1e9) / 1e9,
            step=0.1
        )

        st.success("🎯 Company enrichment complete. Ready for CRQM modeling.")

        # Store output or display
        st.markdown("#### 📄 Finalized Inputs")
        st.write(f"**Ticker:** {ticker}")
        st.write(f"**Name:** {company_data.get('Name')}")
        st.write(f"**Employees:** {employees}")
        st.write(f"**Revenue:** ${revenue:.2f} Billion")
        st.write(f"**Industry:** {company_data.get('Industry')}")
        st.write(f"**Sector:** {company_data.get('Sector')}")
        st.write(f"**Region:** {company_data.get('Region')}")
    else:
        st.error("❌ Could not resolve a valid ticker.")
