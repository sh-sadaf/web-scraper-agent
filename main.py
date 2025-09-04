from scraper import scrape_page
from agent import ask_agent

def main():
    print("Welcome to the Web Scraper + Agent!\n")

    while True:
        url = input("Enter a URL to scrape (or 'exit' to quit): ")
        if url.lower() == "exit":
            break

        # Scrape the new page
        page_data = scrape_page(url)
        print("\nPage scraped successfully.")
        print("Headings found:", page_data['headings'][:10], "...")
        print("Total links found:", len(page_data['links']))

        # Now interactive chat about this page
        while True:
            prompt = input("\nAsk the agent about this page (or 'new' for new page, 'exit' to quit): ")
            if prompt.lower() == "exit":
                return
            if prompt.lower() == "new":
                break  # go back to enter a new URL

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

            User's Question: {prompt}
            """

            answer = ask_agent(context_prompt)
            print("\nAgent answer:\n", answer)

if __name__ == "__main__":
    main()