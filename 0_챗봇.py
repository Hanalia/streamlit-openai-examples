import streamlit as st
from openai import OpenAI


# 메인 함수 정의
def main():
    # 페이지 레이아웃 설정
    st.set_page_config(layout="wide")
    st.title("나의 친근한 AI 챗봇")
    st.caption("스트림릿과 OpenAI API로 챗봇 만들기")

    # 사이드바에 API 키 입력 필드 추가
    with st.sidebar:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="chatbot_api_key", type="password"
        )
        st.markdown(
            "[OpenAI API key 받기](https://platform.openai.com/account/api-keys)"
        )

    # 챗봇 설정 메시지
    system_message = """
    너의 이름은 친구봇이야.
    너는 항상 반말을 하는 챗봇이야. 다나까나 요 같은 높임말로 절대로 끝내지 마
    항상 반말로 친근하게 대답해줘.
    영어로 질문을 받아도 무조건 한글로 답변해줘.
    한글이 아닌 답변일 때는 다시 생각해서 꼭 한글로 만들어줘
    모든 답변 끝에 답변에 맞는 이모티콘도 추가해줘
    """

    # 시스템 메시지 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_message}]

    # 채팅 메시지 표시
    for idx, message in enumerate(st.session_state.messages):
        if idx > 0:  # 시스템 메시지는 표시하지 않음
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    ## 채팅
    prompt = st.chat_input("무엇이 궁금한가요?")

    if prompt:
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        st.session_state["client"] = OpenAI(api_key=openai_api_key)

        # 사용자 메시지 추가 및 표시

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # OpenAI 모델 호출 및 응답 처리
        with st.chat_message("assistant"):
            stream = st.session_state["client"].chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)

        # 어시스턴트 메시지 추가
        st.session_state.messages.append({"role": "assistant", "content": response})

    # 사용자 입력 처리


# 메인 함수 실행
if __name__ == "__main__":
    main()
