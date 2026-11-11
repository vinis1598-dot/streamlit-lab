import streamlit as st
from openai import APIError, NotFoundError

st.title("ChatPDF")
st.session_state.setdefault("pdf_upload_version", 0)


def clear_pdf_chat():
    st.session_state["pdf_session"]["messages"] = []


def leave_pdf():
    pdf = st.session_state["pdf_session"]
    client = pdf["owner_client"]
    pdf["ready"] = False
    pdf["leaving"] = True

    try:
        if pdf["vector_store_id"]:
            try:
                client.vector_stores.delete(
                    vector_store_id=pdf["vector_store_id"]
                )
            except NotFoundError:
                pass
            pdf["vector_store_id"] = None

        if pdf["file_id"]:
            try:
                client.files.delete(pdf["file_id"])
            except NotFoundError:
                pass
            pdf["file_id"] = None

    except APIError as error:
        pdf["error"] = (
            f"삭제 중 오류가 발생했어요. "
            f"Leave를 다시 누르세요. {error}"
        )
        return

    del st.session_state["pdf_session"]
    st.session_state["pdf_upload_version"] += 1


pdf = st.session_state.get("pdf_session")

if pdf is None:
    if "openai_client" not in st.session_state:
        st.info("왼쪽 사이드바에 OpenAI API 키를 입력하세요.")
        st.stop()

    uploaded_file = st.file_uploader(
        "PDF 파일 하나를 선택하세요",
        type=["pdf"],
        accept_multiple_files=False,
        key=f"pdf_upload_{st.session_state['pdf_upload_version']}",
    )

    if uploaded_file is None:
        st.stop()

    client = st.session_state["openai_client"]
    pdf = {
        "owner_client": client,
        "owner_key": st.session_state["api_key"].strip(),
        "filename": uploaded_file.name,
        "vector_store_id": None,
        "file_id": None,
        "ready": False,
        "leaving": False,
        "messages": [],
        "error": None,
    }
    st.session_state["pdf_session"] = pdf

    try:
        with st.spinner("PDF를 업로드하고 검색을 준비하고 있어요."):
            store = client.vector_stores.create(name="ChatPDF")
            pdf["vector_store_id"] = store.id

            uploaded = client.files.create(
                file=(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf",
                ),
                purpose="assistants",
            )
            pdf["file_id"] = uploaded.id

            indexed = client.vector_stores.files.create_and_poll(
                vector_store_id=pdf["vector_store_id"],
                file_id=pdf["file_id"],
            )

            if indexed.status != "completed":
                raise ValueError(
                    f"PDF 분석을 완료하지 못했어요. {indexed.status}"
                )

            pdf["ready"] = True

    except (APIError, ValueError) as error:
        pdf["error"] = str(error)

    st.rerun()

st.button("Clear", on_click=clear_pdf_chat, key="pdf_clear")
st.button("Leave", on_click=leave_pdf, key="pdf_leave")

if pdf["leaving"]:
    st.error(pdf["error"])
    st.stop()

if not pdf["ready"]:
    st.error(pdf["error"] or "PDF 분석을 완료하지 못했어요.")
    st.info("Leave를 눌러 정리한 뒤 PDF를 다시 올리세요.")
    st.stop()

if pdf["owner_key"] != st.session_state.get("api_key", "").strip():
    st.info("API 키가 바뀌었어요. Leave를 누른 뒤 PDF를 다시 올리세요.")
    st.stop()

st.caption(f"현재 PDF · {pdf['filename']}")

for message in pdf["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input(
    "PDF 내용에 대해 질문하세요",
    key="pdf_input",
)

if prompt:
    user_message = {"role": "user", "content": prompt}

    with st.chat_message("user"):
        st.markdown(prompt)

    client = pdf["owner_client"]
    messages = pdf["messages"] + [user_message]

    try:
        with st.chat_message("assistant"):
            with client.responses.create(
                model="gpt-6-luna",
                instructions=(
                    "업로드한 PDF를 검색하여 근거에 따라 한국어로 답하세요. "
                    "PDF에서 확인할 수 없는 내용은 확인할 수 없다고 말하세요."
                ),
                input=messages,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [pdf["vector_store_id"]],
                }],
                tool_choice={"type": "file_search"},
                stream=True,
            ) as stream:
                response = st.write_stream(stream)

    except APIError as error:
        st.error(f"답변 생성 중 오류가 발생했어요. {error}")

    else:
        pdf["messages"].extend([
            user_message,
            {"role": "assistant", "content": response},
        ])