import streamlit as st
from openai import OpenAI
from elevenlabs.client import ElevenLabs


def main():
    st.set_page_config(layout="wide")
    st.title("음성 변환 앱")
    st.caption("텍스트를 음성으로 변환하기")

    with st.sidebar:
        elevenlabs_api_key = st.text_input(
            "ElevenLabs API Key", key="summarizer_api_key", type="password"
        )
        st.markdown(
            "[Elevenlabs API key 받기](https://beta.elevenlabs.io/subscription)"
        )

    default_user_input = """안녕하세요, 여러분. 오늘 우리는 영어에서 자주 사용되는 'Phrasal Verbs'에 대해 배워볼 거예요. Phrasal Verb란 동사와 전치사 또는 부사가 결합하여 새로운 의미를 만드는 표현입니다. 이것은 한국어와는 매우 다른 개념이죠.

Phrasal Verb란 무엇인가? 예: "look up", "turn off", "get along"

Phrasal Verb의 중요성은 일상 대화와 공식적인 글에서 자주 사용된다는 점입니다. 또한 문맥에 따라 의미가 달라질 수 있어요.

예제 문장으로는 다음과 같은 것들이 있습니다:
"I looked up the word in the dictionary." (사전에서 단어를 찾다)
"Could you please turn off the lights?" (불을 꺼 주시겠어요?)
"They get along well with each other." (그들은 서로 잘 지낸다)
        """

    user_input = st.text_area(
        "음성으로 변환할 텍스트를 입력하세요:", value=default_user_input, height=300
    )

    if st.button("음성 생성하기"):
        if not elevenlabs_api_key:
            st.info("계속하려면 API 키를 추가하세요.")
            st.stop()

        if not user_input.strip():
            st.warning("요약할 텍스트를 입력해주세요.")
            st.stop()
        client = ElevenLabs(
            api_key=elevenlabs_api_key,
        )
        try:
            # audio = client.generate(
            #     text=user_input, voice="Rachel", model="eleven_multilingual_v1"
            # )
            # st.audio(data=audio)

            audio_generator = client.generate(
                text=user_input, voice="Chris", model="eleven_multilingual_v2"
            )

            # Convert the generator to bytes
            audio_data = b"".join(audio_generator)

            st.audio(data=audio_data)

        except Exception as e:
            st.exception(f"An error occurred: {e}")
            st.error("다시 시도해 주세요")


if __name__ == "__main__":
    main()
