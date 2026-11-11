import streamlit as st
from openai import OpenAI, APIError


@st.cache_data(show_spinner=False, scope="session")
def get_answer(question, api_key, _client):
    response = _client.responses.create(
        model="gpt-6-luna",
        input=question,
    )
    return response.output_text


st.title("AI 질문 답변")

api_key = st.session_state.get("api_key", "").strip()

if "openai_client" not in st.session_state:
    st.info("왼쪽 사이드바에 OpenAI API 키를 입력하세요.")
    st.stop()
question = st.text_area("질문을 입력하세요").strip()

if st.button("답변 받기"):
    if not question:
        st.warning("질문을 입력하세요.")
        st.stop()

    try:
        with st.spinner("AI가 답변을 만들고 있어요."):
            answer = get_answer(
                question,
                api_key,
                st.session_state["openai_client"],
            )

        st.session_state["last_answer"] = {
            "question": question,
            "answer": answer,
        }
    except APIError as error:
        st.error(f"AI 요청 중 오류가 발생했어요. {error}")

if "last_answer" in st.session_state:
    st.subheader("최근 답변")
    st.write("질문", st.session_state["last_answer"]["question"])
    st.write(st.session_state["last_answer"]["answer"])
import base64

st.divider()
st.subheader("이미지 생성")

prompt = st.text_area(
    "생성할 이미지를 설명하세요",
    key="image_prompt",
)

if st.button("이미지 생성"):
    if not prompt.strip():
        st.warning("이미지 설명을 입력하세요.")
    else:
        try:
            with st.spinner("이미지를 생성하고 있어요."):
                client = st.session_state["openai_client"]

                img = client.images.generate(
                    model="gpt-image-2.6-flare",
                    prompt=prompt,
                )

                image_bytes = base64.b64decode(
                    img.data[0].b64_json
                )

                st.session_state["generated_image"] = {
                    "api_key": api_key,
                    "prompt": prompt,
                    "data": image_bytes,
                }

        except APIError as error:
            st.error(f"이미지 생성 중 오류가 발생했어요. {error}")

if "generated_image" in st.session_state:
    saved_image = st.session_state["generated_image"]

    if saved_image["api_key"] == api_key:
        st.image(
            saved_image["data"],
            caption=saved_image["prompt"],
        )    