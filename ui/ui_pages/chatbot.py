import streamlit as st

from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService

initialize_page(page_header="Chatbot")
data_service = DataService()

st.caption(
    "Ask about rentals, reservations, and inventory, or how to use the app. "
    "For example: *\"Look up rental W0820001\"* or *\"How many scooters are available at each location?\"*"
)

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# render the prior conversation
for message in st.session_state["chat_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# handle a new question
if prompt := st.chat_input("Ask a question..."):
    st.session_state["chat_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # pass the prior history (excluding the just-added user message) for context
            answer = data_service.chat(
                message=prompt,
                history=st.session_state["chat_messages"][:-1],
            )
        if answer is not None:
            st.markdown(answer)
            st.session_state["chat_messages"].append({"role": "assistant", "content": answer})
