import streamlit as st
from openai import OpenAI

with st.sidebar:
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        key="api_key",
    ).strip()

if st.session_state.get("active_api_key") != api_key:
    st.session_state["active_api_key"] = api_key
    st.session_state.pop("openai_client", None)
    st.session_state.pop("last_answer", None)
    st.session_state.pop("generated_image", None)
    st.session_state["chat_messages"] = []

    if api_key:
        st.session_state["openai_client"] = OpenAI(
            api_key=api_key
        )

pg = st.navigation([
    st.Page("app_pages/Home.py", title="Home", icon=":material/home:"),
    st.Page("app_pages/Chat.py", title="Chat", icon=":material/chat:"),
    st.Page("app_pages/Chatbot.py", title="Chatbot", icon=":material/local_library:"),
    st.Page("app_pages/ChatPDF.py", title="ChatPDF", icon=":material/picture_as_pdf:"),
])

pg.run()