import os
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import streamlit as st
import google.generativeai as genai

# --- Gemini Setup ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("⚠️ Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# --- Revenue Formatter ---
def format_revenue(value):
    try:
        value = float(value)
        if value >= 1e12:
            return f"${value/1e12:.2f} Trillion"
        elif value >= 1e9:
            return f"${value/1e9:.2f} Billion"
        elif value >= 1e6:
            return f"${value/1e6:.2f} Million"
        else:
            return f"${value:,.0f}"
    except:
        return value or "Unknown"

# --- Yahoo Finance Fetch ---
def fetch_from_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Name": info.get("longName"),
            "Revenue": info.get("totalRevenue"),
            "Employees": info.get("fullTimeEmployees"),
            "Industry": info.get("industry"),
            "Sector": info.get("sector"),
            "Region": info.get("country")
        }
    except:
        return {}

# --- Screener Fallback ---
def scrape_screener(ticker):
    try:
        url = f"https://www.screener.in/company/{ticker.upper()}/"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        values = {}
        for li in soup.select("section#company-info li"):
            text = li.get_text(strip=True)
            if "Employees" in text:
                values["Employees"] = ''.join(filter(str.isdigit, text))
            if "Industry" in text:
                values["Industry"] = text.split("Industry")[-1].strip(": ")
        return values
    except:
        return {}

# --- Moneycontrol Fallback ---
def scrape_moneycontrol(company_name):
    try:
        search = f"https://www.moneycontrol.com/search/?type=1&search_str={company_name}"
        soup = BeautifulSoup(requests.get(search).text, "html.parser")
        first_result = soup.find("li", class_="clearfix")
        if not first_result:
            return {}
        link = first_result.find("a")["href"]
        soup2 = BeautifulSoup(requests.get(link).text, "html.parser")
        result = {}
        for div in soup2.select("div.FL.gL_10.UC"):
            if "Employees" in div.text:
                result["Employees"] = ''.join(filter(str.isdigit, div.text))
        return result
    except:
        return {}

# --- Merge Strategy ---
def merge_data(primary, fallback1, fallback2):
    fields = ["Name", "Revenue", "Employees", "Industry", "Sector", "Region"]
    out = {}
    for field in fields:
        val = primary.get(field) or fallback1.get(field) or fallback2.get(field) or "Unknown"
        if field == "Revenue":
            val = format_revenue(val)
        out[field] = val
    return out

# --- Gemini Company Options ---
def get_company_options(company_input):
    prompt = f"Suggest 5 companies matching: {company_input}. Format: 1. Name"
    try:
        response = model.generate_content(prompt)
        return [line.split('. ', 1)[-1].strip() for line in response.text.strip().split('\n') if '. ' in line]
    except:
        return []

# --- Gemini Ticker Lookup ---
def get_ticker_from_gemini(company_name):
    prompt = f"""
    What is the official stock ticker (with .NS or .NASDAQ etc) for "{company_name}"?
    Return only the ticker or 'NOT_LISTED'.
    """
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return None

# --- Subsidiaries Finder ---
def get_subsidiaries(company_name):
    prompt = f"""
    List publicly traded subsidiaries of "{company_name}". Format:
    1. TICKER - Name
    """
    try:
        response = model.generate_content(prompt)
        options = []
        for line in response.text.strip().split("\n"):
            if " - " in line:
                parts = line.split(" - ")
                if len(parts) == 2 and "." in parts[0]:
                    options.append((parts[0].split(". ", 1)[-1], parts[1].strip()))
        return options
    except:
        return []

# --- Streamlit App ---
st.set_page_config("CRQM Company Info")
st.title("💼 CRQM – Company Info")

company_input = st.text_input("🔎 Enter company name", "aditya")

if company_input:
    company_options = get_company_options(company_input)
    if not company_options:
        st.error("No suggestions found.")
        st.stop()

    selected_company = st.selectbox("Select intended company", company_options)
    if selected_company:
        ticker = get_ticker_from_gemini(selected_company)

        if ticker and " " not in ticker and "." in ticker:
            st.success(f"✅ Found ticker: {ticker}")
        else:
            st.warning("Company not directly listed. Checking for subsidiaries...")
            subsidiaries = get_subsidiaries(selected_company)
            if not subsidiaries:
                st.error("No subsidiaries found.")
                st.stop()
            sub_choice = st.selectbox("Choose listed subsidiary", [f"{tkr} - {nm}" for tkr, nm in subsidiaries])
            ticker = sub_choice.split(" - ")[0]

        yahoo = fetch_from_yahoo(ticker)
        screener = scrape_screener(ticker)
        money = scrape_moneycontrol(selected_company)

        info = merge_data(yahoo, screener, money)

        st.markdown("### 🧾 Company Snapshot")
        for k, v in info.items():
            st.write(f"**{k}:** {v}")

        st.markdown("---")
        employees = st.slider("🔧 Adjust Employee Count", min_value=1, max_value=1_000_000,
                              value=int(info.get("Employees", 1000)) if str(info.get("Employees", "")).isdigit() else 1000,
                              step=100)
        revenue_float = float(info["Revenue"].split()[0].replace("$", "").replace(",", "")) if info["Revenue"] != "Unknown" else 1.0
        revenue = st.slider("💰 Adjust Revenue (in billions USD)", min_value=0.0, max_value=2000.0,
                            value=revenue_float, step=0.1)

        st.success("✅ Data ready for CRQM modeling.")
