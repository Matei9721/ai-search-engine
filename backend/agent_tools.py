import os

from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import tool
from langchain_community.utilities import SearxSearchWrapper
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer

SERP_API_KEY = os.getenv("SERAPI_TOKEN")

DEPLOY = True
searx_url = "https://docker-searxng-zhsamuchzq-ez.a.run.app" if DEPLOY else "http://localhost:8080/"


@tool
def search_google_serapi(query: str, search_engine: str = "google", location: str = None, hl: str = None,
                         gl: str = None):
    """
    This tool can be used to search the web using the SerpAPI. It can be used to search for any query on the web.
    :param gl: Parameter defines the country to use for the Google search. It's a two-letter country code
    :param hl: Parameter defines the language to use for the Google search. It's a two-letter language code
    :param location: Parameter defines from where you want the search to originate.
    :param query: Parameter defines the query you want to search. You can use anything that you would use in a regular
     Google search.
    :param search_engine: Set parameter to google (default) to use the Google API engine.
    :return: The search results from the SerpAPI in JSON format.
    """

    params = {
      "engine": search_engine,
      "q": query,
      "api_key": os.getenv("SERAPI_TOKEN"),
      "hl": hl,
      "gl": gl,
      "location": location
    }

    search_engine = SerpAPIWrapper(serpapi_api_key=SERP_API_KEY, params=params)

    api_results = search_engine.results(query)

    llm_formatted_results = {}

    if "answer_box" in api_results.keys():
        llm_formatted_results["answer_box"] = api_results["answer_box"]

    if "questions_and_answers" in api_results.keys():
        llm_formatted_results["questions_and_answers"] = api_results["questions_and_answers"]

    search_results = []
    for organic_result in api_results.get("organic_results", []):
        result = {
            "title": organic_result.get("title"),
            "link": organic_result.get("link"),
            "snippet": organic_result.get("snippet")}
        search_results.append(result)

    llm_formatted_results["search_results"] = search_results

    return llm_formatted_results

# Define the tools for the agent to use
@tool
def search_searx(query: str):
    """
    Call to surf the web using searx engine API. There are not additional parameters to be passed to this tool.
    :param query: User query to search on the web
    :return: Dictionary of the web search results
    """
    search_index = SearxSearchWrapper(searx_host=searx_url)

    return search_index.results(
        query,
        num_results=5)


@tool
def search_website_link(url: str):
    """
    This tool can be used to get more information from any webpage (by scraping it). You can scrape any webpage as
    long as you have the URL for it. You can use this function to get more information to answer a user's query.
    :param url: URL of the page we want to scrape to get more information (scrape).
    :return: The contents of the web-page scraped in plain text.
    """
    """"""

    # There is bug where Washington Post website is crashing the application when trying to scrape it
    # TODO: Find better fix for this issue
    if "washingtonpos" in url:
        return "No data on this website"

    try:
        # Load the HTML view of the page
        loader = AsyncHtmlLoader(url)
        doc = loader.load()

        # Transform the HTML to plain text by removing tags
        html2text = Html2TextTransformer()
        doc_transformed = html2text.transform_documents(doc)

        # Return first 10k tokens from the page to avoid blowing up the tokens
        return doc_transformed[0].page_content[:10000]
    except Exception as e:
        return Exception(f"Error occurred when scraping {url}")
