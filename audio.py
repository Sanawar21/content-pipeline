import os
import elevenlabs
from dotenv import load_dotenv
from utils import paths, read_content

load_dotenv()
elevenlabs.set_api_key(os.getenv("ELEVENLABS"))


def clone_voice(name: str, description):
    return elevenlabs.clone(
        name=name, description=description, files=paths.get_input_audios()
    )


def list_voices():
    return [voice.name for voice in elevenlabs.voices()]


def generate_audio(voice: str):
    content = read_content()
    text = content["hook"] + " " + content["script"]
    return elevenlabs.save(elevenlabs.generate(text=text, voice=voice), paths.audio)


if __name__ == "__main__":
    print(list_voices())
