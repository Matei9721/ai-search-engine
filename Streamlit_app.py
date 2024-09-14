import sys
import streamlit as st

from langchain_core.messages import HumanMessage

from backend.web_agent import get_agent
from datamodels.llm_agent_credentials import AgentCredentials

st.set_page_config(layout="wide")

with st.sidebar:
    # Streamlit UI for dynamic configuration
    st.markdown("LLM Configuration")
    llm_provider = st.selectbox(label="Select your LLM provider", options=["GitHubOpenAI", "OpenAI", "AzureOpenAI"],
                                index=0)
    agent_credentials = AgentCredentials()
    if llm_provider == "GitHubOpenAI":
        # Create a checkbox that is on (True) by default
        use_default_token = st.checkbox("Use default token. (Could be broken)", value=True)
        agent_credentials.github_default_token = use_default_token

        agent_credentials.openai_model = st.text_input("OpenAI model", value="gpt-4o-mini")
        # If the checkbox is unchecked, allow user to add their own GitHub token
        if not use_default_token:
            agent_credentials.github_token = st.text_input("GitHub Token", value=None, type="password")
    elif llm_provider == "OpenAI":
        agent_credentials.github_default_token = False
        agent_credentials.openai_model = st.text_input("OpenAI model", value="gpt-4o-mini")
        agent_credentials.openai_key = st.text_input("API Key", value=None, type="password")
    elif llm_provider == "AzureOpenAI":
        agent_credentials.github_default_token = False
        agent_credentials.azure_endpoint = st.text_input("Azure Endpoint", value=None)
        agent_credentials.azure_deployment = st.text_input("Azure Deployment", value=None)
        agent_credentials.api_version = st.text_input("API Version", value=None)
        agent_credentials.api_key = st.text_input("API Key", value=None, type="password")

    st.divider()

    thread = st.number_input("Enter conversation thread id", value=1)

    if st.button("Clear chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello, I am a bot that can search the web. How can I help you?"}]

if agent_credentials.has_any_valid_credentials():
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant",
                                      "content": "Hello, I am a bot that can search the web. How can I help you?"}]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if agent_credentials.has_any_valid_credentials():
    prompt = st.chat_input("Say something")  # Wait for user input

    if prompt:
        # Proceed once the user has provided input
        agent = get_agent(agent_llm_credentials=agent_credentials)

        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.status("Agent is running...", expanded=True):
            inputs = {"messages": [HumanMessage(content=prompt)]}
            config = {"configurable": {"thread_id": thread}}

            response = ""

            # Loop through streaming updates from the graph
            for chunk in agent.stream(inputs, stream_mode="updates", config=config):
                sys.stdout.flush()
                for node, values in chunk.items():
                    response = values['messages'][-1].content
                    if node == "agent":
                        st.write(f"Update from Agent: {values['messages']}")
                    else:
                        st.write(f"Update from Web tools: {values['messages']}")

        with st.chat_message("assistant"):
            st.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.write("Add your LLM provider details before proceeding.")

