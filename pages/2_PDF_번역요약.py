import os
from typing import BinaryIO
import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF library to handle PDF files


## 만약 한글화가 필요한 경우
def style_language_uploader():
    lang = "ko"
    languages = {
        "en": {
            "button": "Browse Files",
            "instructions": "Drag and drop files here",
            "limits": "Limit 200MB per file",
        },
        "ko": {
            "button": "파일 찾아보기",
            "instructions": "여기에 파일을 끌어다 놓으세요",
            "limits": "파일당 200MB 제한",
        },
    }

    hide_label = (
        """
        <style>
            div[data-testid="stFileUploader"]>section[data-testid="stFileUploaderDropzone"]>button[data-testid="baseButton-secondary"] {
               color:white;
            }
            div[data-testid="stFileUploader"]>section[data-testid="stFileUploaderDropzone"]>button[data-testid="baseButton-secondary"]::after {
                content: "BUTTON_TEXT";
                color:black;
                display: block;
                position: absolute;
            }
            div[data-testid="stFileUploaderDropzoneInstructions"]>div>span {
               visibility:hidden;
            }
            div[data-testid="stFileUploaderDropzoneInstructions"]>div>span::after {
               content:"INSTRUCTIONS_TEXT";
               visibility:visible;
               display:block;
            }
             div[data-testid="stFileUploaderDropzoneInstructions"]>div>small {
               visibility:hidden;
            }
            div[data-testid="stFileUploaderDropzoneInstructions"]>div>small::before {
               content:"FILE_LIMITS";
               visibility:visible;
               display:block;
            }
        </style>
        """.replace(
            "BUTTON_TEXT", languages.get(lang).get("button")
        )
        .replace("INSTRUCTIONS_TEXT", languages.get(lang).get("instructions"))
        .replace("FILE_LIMITS", languages.get(lang).get("limits"))
    )

    st.markdown(hide_label, unsafe_allow_html=True)


def extract_text_from_pdf(file):
    document = fitz.open(stream=file.read())
    text = ""
    for page in document:
        text += page.get_text()
    return text


def main():
    st.set_page_config(layout="wide")
    style_language_uploader()
    st.title("PDF문서 번역/요약")
    st.caption("PDF 파일을 업로드해 주세요")

    with st.sidebar:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="summarizer_api_key", type="password"
        )
        st.markdown(
            "[OpenAI API key 받기](https://platform.openai.com/account/api-keys)"
        )

    system_message = """
    너는 문서 요약 전문가야. 주어진 텍스트를 간결하고 명확하게 번역하고 요약해줘.
    - 요약은 항상 한글로 해야 해. 
    - 마크다운과 불렛포인트로 표현해줘
    - 요약은 원문의 핵심 내용을 포함해야 하고, 불필요한 세부사항은 제외해.
    요약 끝에는 적절한 이모티콘을 추가해줘.
    """

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_message}]

    pdf_file = st.file_uploader(
        "PDF 파일을 업로드하세요", type=["pdf"], label_visibility="hidden"
    )
    if pdf_file:
        extracted_text = extract_text_from_pdf(pdf_file)
    else:
        extracted_text = ""  # Default empty text if no file is uploaded

    if st.button("텍스트 요약하기"):
        if not openai_api_key:
            st.info("계속하려면 OpenAI API 키를 추가하세요.")
            st.stop()

        if not extracted_text.strip():
            st.warning("요약할 텍스트를 추출할 PDF 파일을 업로드해주세요.")
            st.stop()

        st.session_state["client"] = OpenAI(api_key=openai_api_key)

        prompt = f"다음 텍스트를 요약해줘:\n\n{extracted_text}"
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("요약 중..."):
            stream = st.session_state["client"].chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
