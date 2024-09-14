from langchain_core.tools import tool
from langchain_community.utilities import SearxSearchWrapper
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer

DEPLOY = True
searx_url = "https://docker-searxng-zhsamuchzq-ez.a.run.app" if DEPLOY else "http://localhost:8080/"


# Define the tools for the agent to use
@tool
def search_searx(query: str):
    """
    Call to surf the web.
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
    This tool can be used to get more information from a specific page if the existing information about that page
    is not enough.
    :param url: URL of the page we want to scrape to get more information.
    :return: The contents of the web-page.
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
