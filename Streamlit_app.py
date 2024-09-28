import sys
import streamlit as st

from langchain_core.messages import HumanMessage

from backend.web_agent import get_agent, reset_memory
from datamodels.llm_agent_credentials import AgentCredentials
from database.chat_database import ChatDatabase
from backend.utils import generate_new_conversation_thread_id

chat_database = ChatDatabase()
st.set_page_config(layout="wide")


def handle_click(key):
    """
    Updates the cached value of the current chat id
    :param key: Chat history id
    :return: None
    """
    st.session_state.selected_key = key


# Initialize session state variable if not set
if 'selected_key' not in st.session_state:
    st.session_state.selected_key = None

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

    st.markdown("Chat Configuration")

    user_identifier = st.text_input("Enter a unique (user) identifier (for chat history to work)", value="default_user")
    initial_thread_value = st.session_state.selected_key if st.session_state.selected_key is not None else 1
    thread = st.number_input("Jump to a conversation id", value=initial_thread_value,
                             on_change=handle_click, args=(None,))

    # Get history data for this user if it exists
    history_data = chat_database.get_all_chats_history_for_user(user_identifier)

    # Start new conversation
    if st.button("Start new chat", type="primary"):
        new_thread_id = generate_new_conversation_thread_id(existing_numbers=history_data["chat_id"], lower_bound=1,
                                                            upper_bound=100)
        handle_click(new_thread_id)
        st.rerun()

    # Try to display all previous conversations of the user
    st.markdown("##### Available chat history for current user")
    with st.container(height=300):
        for conversation_start, conversation_id in zip(history_data["chat_start"], history_data["chat_id"]):
            st.button(f"({conversation_id}) {conversation_start[:50]}...", type="secondary", key=conversation_id,
                      on_click=handle_click, args=(conversation_id,))

    # Reset database
    if st.button("Clear chat"):
        reset_memory()
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello, I am a bot that can search the web. How can I help you?"}]

if agent_credentials.has_any_valid_credentials():
    # Update the thread id with the one selected by the user if any selected
    thread = st.session_state.selected_key if st.session_state.selected_key is not None else thread

    # Get history for this user and this conversation thread
    history = chat_database.chat_history_from_checkpoint(user_identifier=user_identifier, thread=thread)

    # Display chat messages from history on app rerun
    for message in history:
        with st.chat_message(message["role"]):
            print(message["content"])
            st.markdown(message["content"])

if agent_credentials.has_any_valid_credentials():
    prompt = st.chat_input("Say something")  # Wait for user input

    if prompt:
        # Proceed once the user has provided input
        agent = get_agent(agent_llm_credentials=agent_credentials)

        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)

        with st.status("Agent is running...", expanded=True):
            inputs = {"messages": [HumanMessage(content=prompt)]}
            config = {"configurable": {"thread_id": user_identifier + str(thread)}}

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

else:
    st.write("Add your LLM provider details before proceeding.")
