# streamlit_app.py
import streamlit as st
import asyncio
import subprocess
import sys
import os
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from agent import ask_agent  # your existing Gemini agent function

st.title("Web Scraper + AI Chat")

def install_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    try:
        # Try python module first (more reliable on Streamlit Cloud)
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], capture_output=True, text=True, check=True, timeout=300)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        st.warning(f"Playwright installation attempt failed: {str(e)}")
        return False

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    try:
        # Try to import and check if browsers are available
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        st.warning(f"Playwright browser check failed: {str(e)}")
        return False

# Initialize session state
if "page_data" not in st.session_state:
    st.session_state.page_data = None

# Check and install Playwright browsers if needed
playwright_available = check_playwright_browsers()
if not playwright_available:
    st.info("Setting up Playwright browsers... This may take a few minutes on first run.")
    with st.spinner("Installing Playwright browsers..."):
        if install_playwright_browsers():
            st.success("Playwright browsers installed successfully!")
            st.rerun()
        else:
            st.warning("Playwright installation failed, but the app will work with fallback method.")
            st.info("The app will use requests + BeautifulSoup for scraping instead of Playwright.")

# Show scraping method status
if playwright_available:
    st.success("✅ Playwright available - using advanced scraping")
else:
    st.info("ℹ️ Using fallback scraping method (requests + BeautifulSoup)")

# Input URL
url = st.text_input("Webpage URL:")

# Input Question
question = st.text_input("Your Question:")

def scrape_page_fallback(url: str):
    """Fallback scraping method using requests and BeautifulSoup"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get headings
        headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
        
        # Get links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        return {"url": url, "headings": headings, "links": links}
    except Exception as e:
        st.error(f"Error scraping page with fallback method: {str(e)}")
        return None

async def scrape_page(url: str):
    """Scrape the page asynchronously using Playwright with fallback"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set a reasonable timeout
            page.set_default_timeout(30000)
            
            await page.goto(url, wait_until="domcontentloaded")
            
            # Get headings and links
            headings = await page.eval_on_selector_all("h1, h2, h3, h4, h5, h6", "elements => elements.map(e => e.innerText)")
            links = await page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
            await browser.close()
            
            return {"url": url, "headings": headings, "links": links}
    except Exception as e:
        st.warning(f"Playwright scraping failed: {str(e)}")
        st.info("Trying fallback method with requests...")
        return scrape_page_fallback(url)

async def main(url, question):
    if url:
        page_data = await scrape_page(url)
        if page_data:
            st.session_state.page_data = page_data
            st.success("Page scraped successfully!")
            st.write("Headings found:", st.session_state.page_data["headings"])
            st.write("Total links found:", len(st.session_state.page_data["links"]))
        else:
            st.error("Failed to scrape the page. Please check the URL and try again.")

    if question and st.session_state.page_data:
        # Combine page info with user question
        page_text = "\n".join(st.session_state.page_data["headings"])
        prompt = f"Here is the scraped page content:\n{page_text}\n\nUser Question: {question}"
        answer = ask_agent(prompt)
        st.subheader("AI Answer")
        st.write(answer)
    elif question:
        st.warning("Please provide a URL to scrape first.")

# Run asyncio inside Streamlit
if url or question:
    asyncio.run(main(url, question))
