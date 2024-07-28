import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


## 다운로드 버튼으로 전체 페이지가 reload 되는 것을 방지
def parse_schedule(text):
    schedule = {"오전": "", "오후": "", "저녁": ""}
    parts = text.split("morning:")

    if len(parts) > 1:
        morning_part = parts[1]
        afternoon_part = ""
        evening_part = ""

        if "afternoon:" in morning_part:
            morning_part, afternoon_part = morning_part.split("afternoon:", 1)

        if "evening:" in afternoon_part:
            afternoon_part, evening_part = afternoon_part.split("evening:", 1)

        schedule["오전"] = morning_part.strip()
        schedule["오후"] = afternoon_part.strip()
        schedule["저녁"] = evening_part.strip()

    return schedule


## returns alist of dict with images and content
## {time:"morning", "content" : "~~", "image_url" : "~~~"}
def parse_and_generate_images(text, client):

    final_result = []
    schedule_dict = parse_schedule(text)

    # Generate images for each part of the schedule
    for time_of_day, details in schedule_dict.items():
        response = client.images.generate(
            model="dall-e-3", prompt=details, size="1024x1024", quality="standard", n=1
        )
        result_dict = {
            "time": time_of_day,
            "content": details.replace("**", ""),
            "image_url": response.data[0].url,
        }
        final_result.append(result_dict)
    return final_result


def main():
    st.set_page_config(layout="wide")
    st.title("여행일정 짜기")

    with st.sidebar:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="summarizer_api_key", type="password"
        )
        st.markdown(
            "[OpenAI API key 받기](https://platform.openai.com/account/api-keys)"
        )
    ## 개반전용 모드
    if os.environ["DEV_MODE"] == "TRUE":
        openai_api_key = os.getenv("OPENAI_API_KEY")

    system_message = """
    너는 여행계획 작성 전문가야.
    - 입력받은 도시에 대해서 오전, 오후, 저녁으로 나눠서 여행일정 작성해줘
    - 오전, 오후, 저녁 일정은 반드시 morning:, afternoon:, evening:로 시작해야 함
    - 각 일정마다 4줄씩 bullet point로 작성해줘
    - 일정에 대해서만 이야기해줘
    - bullet point로 작성해줘
    - 일정은 구체적이고 친절한 가이드처럼 얘기해줘
    """

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_message}]

    default_user_input = """이스탄불"""

    user_input = st.text_input(
        "여행 가고싶은 도시를 입력해 주세요",
        value=default_user_input,
    )

    if st.button("여행계획 작성하기"):
        if not openai_api_key:
            st.info("계속하려면 OpenAI API 키를 추가하세요.")
            st.stop()

        if not user_input.strip():
            st.warning("요약할 텍스트를 입력해주세요.")
            st.stop()

        st.session_state["client"] = OpenAI(api_key=openai_api_key)

        prompt = f"다음 내용을 바탕으로 여행일정을 작성해줘:\n\n{user_input}"
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("작성 중..."):
            response = st.session_state["client"].chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
            )
            print(response)
            result_text = response.choices[
                0
            ].message.content  ## stream이 아니라 바로 결과를 받기 위해서는 이 방법 이용

            results = parse_and_generate_images(result_text, st.session_state["client"])

            for result in results:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.header(result["time"])
                    st.write(result["content"])
                with col2:
                    st.image(result["image_url"])


if __name__ == "__main__":
    main()
