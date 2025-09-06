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

# Try to import Selenium for better fallback
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

st.title("Web Scraper + AI Chat")

# Removed installation function to prevent loops

def check_playwright_browsers():
    """Simple check if Playwright can be imported"""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False

# Initialize session state
if "page_data" not in st.session_state:
    st.session_state.page_data = None

# Simple check - don't try to launch browser during startup
playwright_available = check_playwright_browsers()

# Show scraping method status
if playwright_available:
    st.success("✅ Playwright available - using advanced scraping")
elif SELENIUM_AVAILABLE:
    st.info("ℹ️ Using Selenium + requests fallback for dynamic content")
else:
    st.info("ℹ️ Using enhanced requests method for static content")

# Input URL
url = st.text_input("Webpage URL:")

# Input Question
question = st.text_input("Your Question:")

def scrape_page_selenium(url: str):
    """Selenium-based scraping for dynamic content"""
    if not SELENIUM_AVAILABLE:
        return None
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        
        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get headings
        heading_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        headings = [h.text.strip() for h in heading_elements if h.text.strip()]
        
        # Get links
        link_elements = driver.find_elements(By.TAG_NAME, "a")
        links = [link.get_attribute("href") for link in link_elements if link.get_attribute("href")]
        
        driver.quit()
        
        return {"url": url, "headings": headings, "links": links}
    except Exception as e:
        st.warning(f"Selenium scraping failed: {str(e)}")
        return None

def scrape_page_requests(url: str):
    """Enhanced requests-based scraping with better headers and content extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get headings
        headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
        headings = [h for h in headings if h]  # Remove empty headings
        
        # Get links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        # Get paragraph text for more content
        paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
        paragraphs = [p for p in paragraphs if len(p) > 20]  # Only meaningful paragraphs
        
        return {
            "url": url, 
            "headings": headings, 
            "links": links,
            "paragraphs": paragraphs[:10]  # First 10 paragraphs
        }
    except Exception as e:
        st.error(f"Error scraping page with requests: {str(e)}")
        return None

def scrape_page_fallback(url: str):
    """Smart fallback that tries Selenium first, then requests"""
    # Try Selenium first for dynamic content
    if SELENIUM_AVAILABLE:
        st.info("Trying Selenium for dynamic content...")
        result = scrape_page_selenium(url)
        if result:
            return result
    
    # Fallback to enhanced requests
    st.info("Using enhanced requests method...")
    return scrape_page_requests(url)

async def scrape_page(url: str):
    """Scrape the page asynchronously using Playwright with fallback"""
    if not playwright_available:
        return scrape_page_fallback(url)
    
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
            
            # Display scraped content
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Headings found:**", len(page_data["headings"]))
                if page_data["headings"]:
                    st.write(page_data["headings"][:5])  # Show first 5 headings
            
            with col2:
                st.write("**Links found:**", len(page_data["links"]))
                if "paragraphs" in page_data and page_data["paragraphs"]:
                    st.write("**Content paragraphs:**", len(page_data["paragraphs"]))
        else:
            st.error("Failed to scrape the page. Please check the URL and try again.")

    if question and st.session_state.page_data:
        # Combine page info with user question
        content_parts = []
        
        if st.session_state.page_data["headings"]:
            content_parts.append("Headings: " + "\n".join(st.session_state.page_data["headings"]))
        
        if "paragraphs" in st.session_state.page_data and st.session_state.page_data["paragraphs"]:
            content_parts.append("Content: " + "\n".join(st.session_state.page_data["paragraphs"][:5]))
        
        page_text = "\n\n".join(content_parts)
        prompt = f"Here is the scraped page content:\n{page_text}\n\nUser Question: {question}"
        answer = ask_agent(prompt)
        st.subheader("AI Answer")
        st.write(answer)
    elif question:
        st.warning("Please provide a URL to scrape first.")

# Run asyncio inside Streamlit
if url or question:
    asyncio.run(main(url, question))
