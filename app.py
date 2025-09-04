from fastapi import FastAPI
from pydantic import BaseModel
from scraper import scrape_page
from agent import ask_agent

app = FastAPI(title="Web Scraper + AI Agent")

# Request model
class QueryRequest(BaseModel):
    url: str
    question: str

@app.get("/")
def root():
    return {"message": "Welcome to Web Scraper + AI Agent API!"}

@app.post("/query")
def query_agent(request: QueryRequest):
    # Scrape the page
    page_data = scrape_page(request.url)

    # Prepare context for AI
    context_prompt = f"""
    You are an AI web analysis agent.
    You have scraped the webpage: {page_data['url']}.

    Page Content Summary:
    - Headings: {page_data['headings']}
    - Example Links: {page_data['links'][:15]} (and more exist on the page)

    Your tasks:
    - Answer the user's question clearly and concisely.
    - If the question is about categories, identify them from headings or links.
    - If the question is about products (like books), try to extract relevant ones.
    - If the question is about summarizing, provide a short summary.
    - If information is missing, say so politely instead of guessing.

    User's Question: {request.question}
    """

    answer = ask_agent(context_prompt)
    return {
        "url": request.url,
        "question": request.question,
        "answer": answer
    }

    

