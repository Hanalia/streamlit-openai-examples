import uuid
from dotenv import load_dotenv
import os
from elevenlabs.client import ElevenLabs

load_dotenv()

# Initialize the client
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

# Dialogue text
dialogue_text = """
지수: 안녕하세요, 민혁씨. 요즘 잘 지내세요?
민혁: 안녕하세요, 지수씨. 네, 잘 지내고 있습니다. 지수씨는요?
지수: 저도 잘 지내고 있어요. 오늘 이야기하고 싶은 주제가 있는데, 바로 생성 AI의 미래에 대해서입니다.
민혁: 아, 생성 AI요? 정말 흥미로운 주제네요. 어떤 부분이 궁금하신가요?
지수: 최근에 생성 AI가 많이 발전하고 있어서 앞으로 어떻게 변할지 궁금해요. 민혁씨는 어떻게 생각하세요?
민혁: 맞아요. 생성 AI는 이미 많은 분야에서 큰 변화를 일으키고 있어요. 예를 들어, 텍스트 생성, 이미지 생성, 음악 생성 등 다양한 응용 분야가 있죠. 앞으로는 더 많은 영역에서 활용될 것 같아요.
지수: 맞아요. 요즘은 예술 분야에서도 생성 AI가 많이 사용되고 있는 것 같아요. 예술가들이 AI를 도구로 사용해서 새로운 작품을 만들기도 하고요.
민혁: 네, 그렇죠. 생성 AI는 창의력을 증진시키는 도구로서의 역할도 할 수 있어요. 예를 들어, 화가가 새로운 아이디어를 얻기 위해 AI를 사용하거나, 작가가 소설의 플롯을 발전시키기 위해 사용할 수 있죠.
지수: 그런데 생성 AI가 너무 발전하면 인간의 창의력이 약해질 수도 있다는 우려도 있지 않나요?
민혁: 그런 우려도 있죠. 하지만 저는 AI와 인간의 협업이 더 중요하다고 생각해요. AI는 도구일 뿐이고, 최종 결정과 창작은 여전히 인간의 몫이니까요.
지수: 그 말도 맞아요. AI가 할 수 없는 부분도 분명 있을 테니까요. 예를 들어, 인간의 감정이나 경험을 바탕으로 한 창작은 아직은 AI가 따라오기 힘들겠죠.
민혁: 맞아요. 그리고 법적, 윤리적 문제도 고려해야 해요. AI가 생성한 작품의 저작권 문제라든가, AI를 악용해서 부정적인 결과를 초래할 가능성도 있죠.
지수: 그렇군요. 그래서 앞으로는 AI의 윤리적인 사용에 대한 논의도 많이 필요할 것 같아요.
민혁: 맞습니다. 그래서 법적 규제와 윤리적인 가이드라인이 중요한 역할을 할 거예요. AI 기술이 발전함에 따라 이에 맞는 새로운 규범이 필요할 겁니다.
지수: 그렇네요. 그리고 교육도 중요한 것 같아요. 사람들이 AI를 어떻게 올바르게 사용할지 배우는 것도 필요하겠죠.
민혁: 네, 맞아요. AI 교육을 통해 사람들이 AI를 이해하고, 이를 활용하는 방법을 배우는 것이 중요해요. 특히 젊은 세대들이 AI 기술에 대해 잘 알고 활용할 수 있도록 교육하는 것이 중요하죠.
지수: 그렇다면, 미래의 생성 AI는 어떤 모습일까요?
민혁: 앞으로는 더욱 정교해지고, 다양한 분야에서 적용될 것입니다. 예를 들어, 개인 맞춤형 콘텐츠 생성, 복잡한 문제 해결, 인간의 삶을 더욱 편리하게 만드는 도구로 발전할 것 같아요.
지수: 정말 기대되네요. 생성 AI가 우리 삶에 긍정적인 영향을 많이 미칠 수 있기를 바랍니다.
민혁: 저도 그래요. 중요한 것은 우리가 AI를 어떻게 사용하느냐에 달려 있을 겁니다. 지수씨, 오늘 정말 유익한 대화였어요.
지수: 저도 많이 배웠어요, 민혁씨. 다음에 또 이런 흥미로운 주제로 이야기 나누면 좋겠어요.
민혁: 네, 언제든지요. 좋은 하루 보내세요, 지수씨.
지수: 민혁씨도요. 안녕히 가세요!
"""

# Parse the dialogue text
dialogues = dialogue_text.strip().split("\n")

# Initialize a list to hold the audio data
audio_clips = []

# Process each line of the dialogue
for dialogue in dialogues:
    speaker, text = dialogue.split(": ", 1)
    voice = "Chris" if speaker == "지수" else "Charlie"
    voice_id = "iP95p4xoKVk53GoZ742B" if voice == "Chris" else "IKne3meq5aSn9XLyUdCD"
    # Generate the audio
    audio_generator = client.text_to_speech.convert(
        voice_id=voice_id,  # Replace with appropriate voice IDs
        output_format="mp3_22050_32",  # MP3 format
        text=text,
        model_id="eleven_multilingual_v2",
    )

    # Convert the generator to bytes
    audio_data = b"".join(audio_generator)

    # Append the audio data to the list
    audio_clips.append(audio_data)

# Concatenate all the audio clips into one audio file
final_audio = b"".join(audio_clips)

# Generate a unique file name for the output MP3 file
save_file_path = f"{uuid.uuid4()}.mp3"

# Save the final audio to a file
with open(save_file_path, "wb") as f:
    f.write(final_audio)

print(f"Audio file generated and saved as '{save_file_path}'.")
