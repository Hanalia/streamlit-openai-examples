import base64
from io import StringIO
import os
import re
from typing import BinaryIO, List
from dotenv import load_dotenv
import pandas as pd
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
            "instructions": "여기에 이미지를 끌어다 놓으세요",
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


def markdown_to_dataframes(markdown_text):
    # Regular expression to find markdown tables
    table_pattern = r"\|(.+)\|\n\|(-+\|)+\n(((\|.+\|\n)+\|.+\|)\n?)"

    # Find all tables in the markdown text
    tables = re.findall(table_pattern, markdown_text)

    dataframes = []

    for table in tables:
        # Extract header and data rows
        header = table[0].strip().split("|")
        data_rows = table[2].strip().split("\n")

        # Clean up header and data
        header = [h.strip() for h in header if h.strip()]
        data = [
            [cell.strip() for cell in row.split("|") if cell.strip()]
            for row in data_rows
        ]

        # Check for duplicate column names and modify them
        column_counts = {}
        new_header = []
        for col in header:
            if col in column_counts:
                column_counts[col] += 1
                new_col_name = f"{col}_{column_counts[col]}"
            else:
                column_counts[col] = 0
                new_col_name = col
            new_header.append(new_col_name)

        # Create DataFrame
        df = pd.DataFrame(data, columns=header)
        dataframes.append(df)
    return dataframes


## openai 에 이미지를 업로드하기 위해서는 base64 인코딩이 필요함


def encode_image(image: BinaryIO):
    return base64.b64encode(image.read()).decode("utf-8")


def extract_text_from_pdf(file):
    document = fitz.open(stream=file.read())
    text = ""
    for page in document:
        text += page.get_text()
    return text


def main():
    st.set_page_config(layout="wide")
    style_language_uploader()
    st.title("이미지로 된 데이터 분석하기")
    st.caption("분석할 이미지를 업로드해 주세요")

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

    image_file = st.file_uploader(
        "이미지를 업로드하세요", type=["jpg", "jpeg", "png"], label_visibility="hidden"
    )
    if st.button("AI 분석하기"):
        if not openai_api_key:
            st.info("계속하려면 OpenAI API 키를 추가하세요.")
            st.stop()
        if not image_file:
            st.warning("이미지를 업로드해주세요.")
            st.stop()

        st.session_state["client"] = OpenAI(api_key=openai_api_key)
        with st.spinner("데이터 분석중."):

            base64_image = encode_image(image_file)
            image_url = f"data:image/jpeg;base64,{base64_image}"
            # - 시각화 방법을 제안해 주세요 (line, bar, area)

            prompt = f"""
            너는 최고의 데이터 분석가야
            - 데이터를 분석해서 핵심 내용을 정리한 표와 그에 대한 인사이트를 같이 보여줘
            - 표는 MECE하게 정리해 줘
            - 최소한 2가지 이상의 인사이트를 줘
            - 분석결과만 응답해줘
            """
            response = st.session_state["client"].chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                },
                            },
                        ],
                    }
                ],
                stream=True,
            )
            final_response = st.write_stream(response)
            st.header("데이터 다운로드하기")
            dataframes = markdown_to_dataframes(final_response)

            for df in dataframes:
                st.dataframe(df)


if __name__ == "__main__":
    main()
