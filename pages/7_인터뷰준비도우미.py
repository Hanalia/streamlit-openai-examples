import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI


load_dotenv()


def main():
    st.set_page_config(layout="wide")
    st.title("인터뷰준비 도우미")

    with st.sidebar:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="summarizer_api_key", type="password"
        )
        openai_api_key = os.getenv("OPENAI_API_KEY")

        st.markdown(
            "[OpenAI API key 받기](https://platform.openai.com/account/api-keys)"
        )

    if os.environ["DEV_MODE"] == "TRUE":
        openai_api_key = os.getenv("OPENAI_API_KEY")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    default_user_input = """데이터분석가 직무 정보:
1. 주요 업무
   - 데이터 수집 및 정제: 다양한 소스에서 데이터 수집하고, 분석 가능한 형태로 정제함.
   - 데이터 분석: 통계, 머신러닝, 인공지능 기법 활용해 데이터 분석하고 패턴 찾음.
   - 시각화 및 보고: 분석 결과 이해하기 쉽게 시각화하고, 보고서 작성해 의사결정자에게 전달함.
   - 비즈니스 문제 해결: 데이터 통해 비즈니스 문제 해결하고, 전략 수립하며 성과 향상시킴.
   - 협업: 타 부서와 협력해 데이터 기반 의사결정 지원함.
2. 필요 역량
   - 기술적 역량: 통계학, 수학, 프로그래밍 언어(R, Python 등), 데이터베이스 관리(SQL 등), 데이터 시각화 도구(Tableau, Power BI 등) 기술 필요함.
   - 문제 해결 능력: 데이터 통해 비즈니스 문제 분석하고 해결책 제시할 수 있는 능력 중요함.
   - 비즈니스 이해력: 분석 결과를 비즈니스 맥락에서 해석하고 응용할 수 있는 능력 필요함.
   - 커뮤니케이션 능력: 분석 결과 명확하고 이해하기 쉽게 전달할 수 있는 능력 중요함."""

    user_input = st.text_area(
        "직무 정보를 입력하세요:", value=default_user_input, height=300
    )

    if st.button("예상질문 및 모범답안 생성하기"):
        if not openai_api_key:
            st.info("계속하려면 OpenAI API 키를 추가하세요.")
            st.stop()

        if not user_input.strip():
            st.warning("요약할 텍스트를 입력해주세요.")
            st.stop()

        st.session_state["client"] = OpenAI(api_key=openai_api_key)

        prompt = f"""
        너는 전문 채용 컨설턴트야문서 요약 전문가야. 주어진 직무정보를 기반으로 면접질문과 모범답안, 핵심 준비포인트를 작성해줘
        - 마크다운 표로 보여줘
        - 모범답안은 두괄식 1문장, 근거 3문장으로 작성해줘
        - 결과만 보여줘
        직무정보 : {user_input} """

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("요약 중..."):
            stream = st.session_state["client"].chat.completions.create(
                model="gpt-4o",
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
