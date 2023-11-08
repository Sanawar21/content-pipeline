import os
import math
import requests
from dotenv import load_dotenv
from utils import paths, read_content
from pydub import AudioSegment


load_dotenv()
API_KEY = os.getenv("ELEVENLABS")
BASE_URL = "https://api.elevenlabs.io"


def split_into_audios():
    audio = AudioSegment.from_wav(paths.input_audio)
    size = 10000  # 50 seconds
    count = math.floor(len(audio)/size)

    for i in range(count):
        start_time = i * size
        end_time = (i + 1) * size
        segment = audio[start_time:end_time]
        output_file = f"{paths.inputs_folder}//audio_{str(i + 1).zfill(4)}.wav"
        segment.export(output_file, format="wav")

    if len(audio) % (count * size):
        last_segment = audio[len(audio) - (len(audio) % (count * size)):]
        output_file = f"{paths.inputs_folder}//audio_{str(count + 1).zfill(4)}.wav"
        last_segment.export(output_file, format="wav")


def clone(name, description=None):
    endpoint = f"{BASE_URL}/v1/voices/add"
    split_into_audios()
    files = [('files', (path, open(path, 'rb')))
             for path in paths.get_input_audios()]
    data = {
        "name": name,
        "description": description,
    }
    response = requests.post(
        endpoint, headers={"xi-api-key": API_KEY}, data=data, files=files)

    if "voice_id" not in dict(response.json()).keys():
        raise Exception(response.json())


def generate(voice_name):
    content = read_content()
    text = content["hook"] + " " + content["script"]
    headers = {"xi-api-key": API_KEY}
    voice_id = list_voices()[voice_name]
    settings = requests.get(
        f"{BASE_URL}/v1/voices/{voice_id}/settings", headers=headers).json()
    endpoint = f"{BASE_URL}/v1/text-to-speech/{voice_id}"

    data = dict(
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=settings,
    )
    try:
        response = requests.post(
            endpoint, headers=headers,  json=data)
        with open(paths.audio, "wb") as file:
            file.write(response.content)
    except:
        raise Exception(str(response.json()))


def list_voices():
    try:
        endpoint = f"{BASE_URL}/v1/voices"
        response = requests.get(endpoint, headers={"xi-api-key": API_KEY})
        voices = response.json()["voices"]
        return {voice["name"]: voice["voice_id"] for voice in voices}
    except:
        raise Exception(str(response.json()))


if __name__ == "__main__":
    split_into_audios()
    # response = generate("Thomas", "This is a test.")
    # with open("output_.mp3", "wb") as file:
    #     file.write(response)


# import os
# import elevenlabs
# from dotenv import load_dotenv
# from utils import paths, read_content

# load_dotenv()
# elevenlabs.set_api_key(os.getenv("ELEVENLABS"))


# def clone_voice(name: str, description):
#     return elevenlabs.clone(
#         name=name, description=description, files=paths.get_input_audios()
#     )


# def list_voices():
#     return [voice.name for voice in elevenlabs.voices()]


# def generate_audio(voice: str):
#     content = read_content()
#     text = content["hook"] + " " + content["script"]
#     return elevenlabs.save(elevenlabs.generate(text=text, voice=voice), paths.audio)


# if __name__ == "__main__":
#     generate_audio("Thomas")
