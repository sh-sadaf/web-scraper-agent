# streamlit_app.py
import streamlit as st
import asyncio
import subprocess
import sys
import os
from playwright.async_api import async_playwright
from agent import ask_agent  # your existing Gemini agent function

st.title("Web Scraper + AI Chat")

def install_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    try:
        # Try to run playwright install
        result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                              capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to install Playwright browsers: {e}")
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
    except Exception:
        return False

# Initialize session state
if "page_data" not in st.session_state:
    st.session_state.page_data = None

# Check and install Playwright browsers if needed
if not check_playwright_browsers():
    st.info("Installing Playwright browsers... This may take a few minutes on first run.")
    if install_playwright_browsers():
        st.success("Playwright browsers installed successfully!")
        st.rerun()
    else:
        st.error("Failed to install Playwright browsers. Please run 'playwright install' manually.")
        st.stop()

# Input URL
url = st.text_input("Webpage URL:")

# Input Question
question = st.text_input("Your Question:")

async def scrape_page(url: str):
    """Scrape the page asynchronously using Playwright"""
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
        st.error(f"Error scraping page: {str(e)}")
        return None

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
