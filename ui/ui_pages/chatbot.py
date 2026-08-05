import streamlit as st

from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService

initialize_page(page_header="Chatbot")
data_service = DataService()

st.caption(
    "Ask about rentals, reservations, and inventory, or how to use the app. "
    "For example: *\"Look up rental W0820001\"* or *\"How many scooters are available at each location?\"*"
)
st.warning("This chatbot is powered by AI and may occasionally make mistakes. Always verify important information.")

EMPTY_TOKEN_USAGE = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "total_tokens": 0}

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []
if "chat_token_usage" not in st.session_state:
    st.session_state["chat_token_usage"] = dict(EMPTY_TOKEN_USAGE)


def clear_chat():
    """Discard the conversation so the next question starts with no history."""
    st.session_state["chat_messages"] = []
    st.session_state["chat_token_usage"] = dict(EMPTY_TOKEN_USAGE)


# render the prior conversation
for message in st.session_state["chat_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("model"):
            st.caption(f"Model: {message['model']}")

# handle a new question
if prompt := st.chat_input("Ask a question..."):
    st.session_state["chat_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # pass the prior history (excluding the just-added user message) for context - only role/content
            # are sent, since ChatMessage forbids the extra "model" key stored on assistant messages
            history = [
                {"role": message["role"], "content": message["content"]}
                for message in st.session_state["chat_messages"][:-1]
            ]
            chat_response = data_service.chat(message=prompt, history=history)
        if chat_response is not None:
            st.markdown(chat_response.answer)
            st.caption(f"Model: {chat_response.model}")
            st.session_state["chat_messages"].append({
                "role": "assistant", "content": chat_response.answer, "model": chat_response.model
            })
            for field in EMPTY_TOKEN_USAGE:
                st.session_state["chat_token_usage"][field] += getattr(chat_response, field)
            # rerun so the clear chat button and token caption below pick up the new state
            st.rerun()

tokens_col, clear_col = st.columns([3, 1], vertical_alignment="bottom")
usage = st.session_state["chat_token_usage"]
tokens_col.caption(
    f"Tokens used this conversation — input: {usage['input_tokens']:,}, output: {usage['output_tokens']:,}, "
    f"cache: {usage['cache_read_tokens']:,}, total: {usage['total_tokens']:,}"
)
clear_col.button(
    label="Clear Chat",
    width="stretch",
    icon=":material/delete_sweep:",
    key="clear_chat",
    disabled=not st.session_state["chat_messages"],
    on_click=clear_chat,
)
