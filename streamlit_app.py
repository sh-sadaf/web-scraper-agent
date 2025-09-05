import streamlit as st
from scraper import scrape_page
from agent import ask_agent

st.set_page_config(page_title="Web Scraper + AI Chat", layout="wide")
st.title("🌐 Web Scraper + AI Chat")

st.markdown("""
Enter a URL of the webpage you want to scrape and ask any question about it. 
The AI agent will try to answer based on the scraped content.
""")

# Input fields
url = st.text_input("🌐 Webpage URL")
question = st.text_input("❓ Your Question")

if st.button("Ask AI"):
    if not url or not question:
        st.warning("Please provide both URL and a question.")
    else:
        try:
            # Scrape the page
            page_data = scrape_page(url)
            st.subheader("📄 Page Summary")
            st.write(f"Headings found: {page_data['headings'][:10]} ...")
            st.write(f"Total links found: {len(page_data['links'])}")

            # Prepare prompt for AI
            context_prompt = f"""
            You are an AI web analysis agent.
            You have scraped the webpage: {url}.

            Page Content Summary:
            - Headings: {page_data['headings']}
            - Example Links: {page_data['links'][:15]} (and more exist on the page)

            User's Question: {question}
            """

            # Get AI answer
            answer = ask_agent(context_prompt)
            st.subheader("🤖 AI Answer")
            st.write(answer)

        except Exception as e:
            st.error(f"Error scraping page or contacting AI: {e}")
