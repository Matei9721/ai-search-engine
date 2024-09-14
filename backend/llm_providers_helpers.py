import os

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from datamodels.llm_agent_credentials import AgentCredentials

# Load environment variables from .env file
load_dotenv()
default_github_token = os.getenv("DEFAULT_GITHUB_TOKEN")

def get_chat_model(agent_llm_credentials: AgentCredentials):
    """
    Returns a chat LLM model depending on the configuration received from the UI
    :param agent_llm_credentials: Dataclass containing credentials based on the UI
    :return: LLM model from different providers
    """
    if agent_llm_credentials.has_valid_openai_credentials():
        return ChatOpenAI(
            api_key=agent_llm_credentials.openai_key,
            model=agent_llm_credentials.openai_model,
            temperature=0
        )
    elif agent_llm_credentials.has_valid_azure_credentials():
        return AzureChatOpenAI(
            azure_endpoint=agent_llm_credentials.azure_endpoint,
            openai_api_version=agent_llm_credentials.api_version,
            azure_deployment=agent_llm_credentials.azure_deployment,
            api_key=agent_llm_credentials.api_key
        )
    elif agent_llm_credentials.has_valid_github_credentials():
        github_token_api_key = default_github_token if agent_llm_credentials.github_default_token\
            else agent_llm_credentials.github_token

        return ChatOpenAI(
            api_key=github_token_api_key,
            base_url="https://models.inference.ai.azure.com",
            model=agent_llm_credentials.openai_model,
            temperature=0
        )

    raise Exception("Current LLM configuration not valid!")
