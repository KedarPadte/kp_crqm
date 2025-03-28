import streamlit as st
import yfinance as yf
import google.generativeai as genai
import os

# Set up Streamlit page
st.set_page_config(page_title="CRQM Company Profiler", layout="wide")
st.title("CRQM – Company Info")

# Load Gemini API key securely
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# --- Utils ---
def format_revenue(val):
    try:
        val = float(val)
        if val >= 1e12:
            return f"${val/1e12:.2f} Trillion"
        elif val >= 1e9:
            return f"${val/1e9:.2f} Billion"
        elif val >= 1e6:
            return f"${val/1e6:.2f} Million"
        return f"${val:,.0f}"
    except:
        return val

# --- Gemini Disambiguation ---
def get_company_options(user_input):
    prompt = f"""The user typed "{user_input}". Suggest a list of real companies or groups they could mean. 
Return only a clean, newline-separated list of exact company names. No comments."""
    try:
        response = model.generate_content(prompt)
        return [line.strip("-•12345. ").strip() for line in response.text.split("\n") if line.strip()]
    except:
        return []

def get_stock_ticker(company_name):
    prompt = f"""Return ONLY the correct official stock ticker (with exchange suffix, e.g., SBIN.NS, AAPL, GOOG) for:
    "{company_name}" 
Only the ticker. No extra text."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip().split()[0]
    except:
        return None

def get_subsidiary_tickers(parent_company):
    prompt = f"""The user searched for "{parent_company}", which is not publicly listed.
List all **publicly listed subsidiaries** (on any exchange) and their correct stock tickers in format: 
TICKER - Company Name. Do not include unlisted firms or comments."""
    try:
        response = model.generate_content(prompt)
        return [line.strip() for line in response.text.split("\n") if line.strip() and "-" in line]
    except:
        return []

# --- Yahoo Finance Fetch ---
def fetch_company_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Name": info.get("longName", "N/A"),
            "Revenue": info.get("totalRevenue", None),
            "Employees": info.get("fullTimeEmployees", None),
            "Industry": info.get("industry", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Region": info.get("country", "N/A")
        }
    except Exception as e:
        return {"Error": str(e)}

# --- Streamlit UI Flow ---
user_input = st.text_input("🔍 Enter company name", placeholder="e.g. SBI, Aditya Birla, Google")

if user_input:
    options = get_company_options(user_input)

    if options:
        company_selected = st.selectbox("Select intended company", options)
        ticker = get_stock_ticker(company_selected)

        if not ticker or " " in ticker or len(ticker) > 15:
            st.warning("Company not directly listed. Checking for subsidiaries...")
            subs = get_subsidiary_tickers(company_selected)
            if subs:
                sub_selected = st.selectbox("Select subsidiary", subs)
                ticker = sub_selected.split(" - ")[0].strip()
            else:
                st.error("No subsidiaries found.")
                st.stop()

        st.success(f"Finalized Ticker: `{ticker}`")
        data = fetch_company_info(ticker)

        if "Error" in data:
            st.error(data["Error"])
            st.stop()

        # Override fields
        st.markdown("### Company Profile")

        st.markdown(f"**Company:** {data['Name']}")
        st.markdown(f"**Region:** {data['Region']}")
        st.markdown(f"**Industry:** {data['Industry']}")
        st.markdown(f"**Sector:** {data['Sector']}")

        revenue_override = st.number_input(
            "Estimated Revenue (override if needed)",
            min_value=0.0,
            step=0.1,
            value=(float(data["Revenue"]) / 1e9) if data["Revenue"] else 1.0,
            help="In USD billions"
        )

        employees_override = st.number_input(
            "👥 Estimated Employees (override if needed)",
            min_value=0,
            value=data["Employees"] if data["Employees"] else 1000,
        )

        st.success("Data loaded and editable. Ready for CRQM modeling.")
    else:
        st.error("Could not find company options.")
