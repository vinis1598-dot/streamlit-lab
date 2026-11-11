import streamlit as st
from openai import APIError

st.title("Chat")

if "openai_client" not in st.session_state:
    st.info("왼쪽 사이드바에 OpenAI API 키를 입력하세요.")
    st.stop()

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []


def clear_chat():
    st.session_state["chat_messages"] = []


st.button("Clear", on_click=clear_chat)

for message in st.session_state["chat_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("메시지를 입력하세요")

if prompt:
    user_message = {"role": "user", "content": prompt}

    with st.chat_message("user"):
        st.markdown(prompt)

    client = st.session_state["openai_client"]
    messages = st.session_state["chat_messages"] + [user_message]

    try:
        with st.chat_message("assistant"):
            with client.responses.create(
                model="gpt-6-luna",
                input=messages,
                stream=True,
            ) as stream:
                response = st.write_stream(stream)

    except APIError as error:
        st.error(f"답변 생성 중 오류가 발생했어요. {error}")

    else:
        st.session_state["chat_messages"].extend([
            user_message,
            {"role": "assistant", "content": response},
        ])