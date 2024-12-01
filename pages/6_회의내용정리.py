import os
from typing import BinaryIO
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF library to handle PDF files

load_dotenv()


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
            "instructions": "여기에 mp3 파일을 끌어다 놓으세요",
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
    st.title("회의내용 AI로 정리")
    st.caption("회의내용 음성 파일을 업로드해 주세요")

    with st.sidebar:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="summarizer_api_key", type="password"
        )

        st.markdown(
            "[OpenAI API key 받기](https://platform.openai.com/account/api-keys)"
        )
    if os.environ["DEV_MODE"] == "TRUE":
        openai_api_key = os.getenv("OPENAI_API_KEY")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    mp3_file = st.file_uploader(
        "mp3 파일을 업로드하세요", type=["mp3"], label_visibility="hidden"
    )
    if st.button("AI 분석하기"):
        if not openai_api_key:
            st.info("계속하려면 OpenAI API 키를 추가하세요.")
            st.stop()
        if not mp3_file:
            st.warning("mp3 파일을 업로드해주세요.")
            st.stop()

        st.session_state["client"] = OpenAI(api_key=openai_api_key)
        with st.spinner("텍스트 추출 및 요약 중..."):
            transcription = st.session_state["client"].audio.transcriptions.create(
                model="whisper-1", file=mp3_file, response_format="text"
            )
            tab1, tab2 = st.tabs(["원본 음성", "텍스트 요약"])
            with tab1:
                st.text_area("Transcribed Text", value=transcription, height=300)

            with tab2:
                initial_prompt = """
                다음 회의록을 요약해줘
                - 마크다운으로 요약해줘
                """
                prompt = f"{initial_prompt}\n\n{transcription}"
                st.session_state.messages.append({"role": "user", "content": prompt})

                response = st.session_state["client"].chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                )
                result_text = response.choices[
                    0
                ].message.content  ## stream이 아니라 바로 결과를 받기 위해서는 이 방법 이용
                st.write(result_text)


if __name__ == "__main__":
    main()
