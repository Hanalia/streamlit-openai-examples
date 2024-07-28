from email.header import decode_header
from typing import Any, Dict, List
import streamlit as st
import pandas as pd
from openai import OpenAI
import imaplib
import email
from dotenv import load_dotenv
import os
import re
from email.message import EmailMessage
from dateutil import parser
from zoneinfo import ZoneInfo
import smtplib

load_dotenv()


def create_reply(
    email_message: email.message.Message, reply_message: str, from_addr: str
) -> EmailMessage:
    reply_to = email_message.get("Reply-To", email_message["From"])
    reply = EmailMessage()
    reply["To"] = reply_to
    reply["From"] = from_addr
    reply["Subject"] = "Re: " + email_message["Subject"]
    reply["In-Reply-To"] = email_message["Message-ID"]
    reply["References"] = (
        email_message.get("References", "") + " " + email_message["Message-ID"]
    ).strip()
    reply.set_content(reply_message)
    return reply


def send_email(message: EmailMessage):
    smtp_server = "smtp.naver.com"
    port = 587
    username = os.getenv("NAVER_EMAIL")
    password = os.getenv("NAVER_PASSWORD")
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(message)


def parse_to_kst(date_string):
    try:
        # Parse the date string
        dt = parser.parse(date_string)

        # If the parsed date doesn't have a timezone, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to KST
        kst_dt = dt.astimezone(ZoneInfo("Asia/Seoul"))

        # Format as "yy.mm hh:mm"
        return kst_dt.strftime("%m.%d %H:%M")
    except Exception as e:
        return f"Error parsing: {e}"


## Substack <no-reply@substack.com> -> ["Substack", "no-reply@substack.com"]
def format_email(input_text: str) -> List[str]:

    # Use a regular expression to find the email part enclosed in angle brackets
    match = re.search(r"<(.+)>", input_text)

    if match:
        email = match.group(1)
        name_part = input_text.replace(f"<{email}>", "").strip().replace('"', "")
        if name_part:
            return [name_part, email]
        else:
            return [None, email]
    else:
        # If no angle brackets, assume the whole input is the email
        return [input_text, input_text]


def decode_mime_words(encoded_string):
    if encoded_string is None:
        return ""  # Return empty string if the input is None
    decoded_words = decode_header(encoded_string)
    decoded_string = ""
    for content, charset in decoded_words:
        if isinstance(content, bytes):  # Check if content is bytes
            if charset:
                decoded_string += content.decode(charset)
            else:
                decoded_string += content.decode(
                    "utf-8"
                )  # Fallback to utf-8 if charset is None
        else:
            decoded_string += content
    return decoded_string


def get_email_content(message):
    if message.is_multipart():
        parts = [get_email_content(part) for part in message.get_payload()]
        return "\n".join(parts)
    else:
        content_type = message.get_content_type()
        if "text/plain" in content_type:
            return message.get_payload(decode=True).decode(
                "utf-8"
            )  # Decode the payload explicitly
        return ""


def show_emails_df(df):
    return st.dataframe(
        df[["날짜", "발신인", "제목"]],
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        # width=100,
        use_container_width=True,
    )


# @st.cache_data
def fetch_emails(email_id: str, email_password: str) -> pd.DataFrame:
    try:
        mail = imaplib.IMAP4_SSL("imap.naver.com")
        mail.login(email_id, email_password)
        mail.select("inbox")

        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()[-30:]
        fetched_emails: List[Dict[str, Any]] = []
        for mail_id in mail_ids:
            result, data = mail.fetch(mail_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            email_data = {
                "날짜": parse_to_kst(msg.get("Date")),
                "발신인": format_email(decode_mime_words(msg.get("From")))[0],
                "sender_email": format_email(decode_mime_words(msg.get("From")))[1],
                "제목": decode_mime_words(msg.get("Subject")),
                "Content": get_email_content(msg),
                "raw_email": raw_email,  # Store the raw email message
            }
            fetched_emails.append(email_data)

        # Convert to DataFrame and sort by 날짜 in descending order
        df = pd.DataFrame(fetched_emails)
        df["날짜"] = pd.to_datetime(df["날짜"], format="%m.%d %H:%M")
        df = df.sort_values(by="날짜", ascending=False)
        df["날짜"] = df["날짜"].dt.strftime("%m.%d %H:%M")

        return df
    except Exception as e:
        st.error(f"이메일 로딩 중 오류가 발생했습니다: {str(e)}")
        return None


def main():
    st.set_page_config(layout="wide")
    st.title("이메일 응답 자동화 앱")
    st.caption("스트림릿과 OpenAI API를 사용하여 이메일 드래프트 생성")

    with st.sidebar:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="summarizer_api_key", type="password"
        )

        email_id = st.text_input("네이버 이메일주소", key="email_id")

        email_password = st.text_input(
            "네이버 이메일 비밀번호", key="email_password", type="password"
        )

    if os.environ["DEV_MODE"] == "TRUE":
        openai_api_key = os.getenv("OPENAI_API_KEY")
        email_id = os.getenv("NAVER_EMAIL")
        email_password = os.getenv("NAVER_PASSWORD")

    if "client" not in st.session_state:
        st.session_state["client"] = OpenAI(api_key=openai_api_key)
    if "answer_generated" not in st.session_state:
        st.session_state["answer_generated"] = False
    col1, col2 = st.columns([1.5, 1])

    with col1:
        if st.button("이메일 불러오기"):
            if not (openai_api_key and email_id and email_password):
                st.info("apikey, 이메일주소, 비밀번호을 입력해 주세요.")
                st.stop()

            with st.spinner("이메일 불러오는 중"):
                emails_df = fetch_emails(email_id, email_password)
                if emails_df is not None:
                    st.session_state["emails"] = emails_df

        if "emails" in st.session_state:
            selected_email = show_emails_df(st.session_state["emails"])

            if selected_email["selection"]["rows"]:
                selected_indices = selected_email["selection"]["rows"]
                selected_index = selected_indices[0]  # Assuming single-row selection
                selected_row = st.session_state["emails"].iloc[selected_index]
                sender_name = selected_row["발신인"]
                sender_email = selected_row["sender_email"]
                email_subject = selected_row["제목"]
                email_content = selected_row["Content"]
                raw_email = selected_row["raw_email"]  # Retrieve raw email

                st.write("제목: " + email_subject)
                st.write("발신인: " + sender_name)
                st.write("발신이메일: " + sender_email)
                st.write(email_content)

            else:
                st.write("이메일을 선택해 주세요")
    with col2:
        default_user_prompt = """- 반드시 한글로 작성해줘
- 구체적인 상황을 설명해달라는 내용을 회신해줘
- 친절하게 작성해 줘"""

        user_input = st.text_area(
            "이메일 답변 방식을 정해주세요", value=default_user_prompt, height=100
        )

        generate_answers = st.button("답변 초안 작성하기")

        if generate_answers:
            with st.spinner("AI 초안 작성 중"):
                prompt = f"""

                    이메일 발신자 : {sender_name}
                    이메일 내용 : {email_content} 
                    너는 위 이메일에 대해서 답변을 작성하는 사람이야 
                    {user_input}
                    """
                response = st.session_state["client"].chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": prompt}],
                )
                result_text = response.choices[
                    0
                ].message.content  ## stream이 아니라 바로 결과를 받기 위해서는 이 방법 이용
            st.session_state["generated_answer"] = result_text
            st.session_state["answer_generated"] = True

        if st.session_state["answer_generated"]:

            st.session_state["final_reply"] = st.text_area(
                "AI로 작성된 초안",
                value=st.session_state["generated_answer"],
                height=300,
            )
            if st.button("메일 회신하기"):
                with st.spinner("메일 회신 중"):
                    email_message = email.message_from_bytes(
                        raw_email
                    )  # Original email message
                    from_addr = email_id  # The email address to send from
                    reply_message = st.session_state[
                        "final_reply"
                    ]  # The edited draft content

                    reply_email = create_reply(email_message, reply_message, from_addr)
                    send_email(reply_email)

                st.success("이메일을 성공적으로 보냈습니다.")


if __name__ == "__main__":
    main()
