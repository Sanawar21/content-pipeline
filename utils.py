import os
import shutil
import pathlib
import json


class Status:
    def __init__(self) -> None:
        self.now = self.off

    def set(self, status: str):
        self.now = status

    done = "done"
    generating_audio = "generating_audio"
    generating_lipsync = "generating_lipsync"
    enhancing_video = "enhancing_video"
    zooming_video = "zooming_video"
    adding_brolls = "adding_brolls"
    generating_subtitles = "generating_subtitles"
    combining_audio_video = "combining_audio_video"
    busy = "busy"
    free = "free"
    off = "off"


class Paths:
    base_path = pathlib.Path(__file__).parent.resolve()

    inputs_folder = base_path / "inputs"
    input_audio = inputs_folder / "_audio.wav"
    input_video = inputs_folder / "video.mp4"
    content_path = inputs_folder / "content.json"

    outputs_folder = base_path / "outputs"
    b_rolls_folder = outputs_folder / "b_rolls"
    preprocessed_video = outputs_folder / "preprocessed.mp4"
    output_video = outputs_folder / "video.mp4"
    enhanced_video = outputs_folder / "enhanced.mp4"
    captioned_video = outputs_folder / "captioned.mp4"
    zoomed_video = outputs_folder / "zoomed.mp4"
    b_rolled_video = outputs_folder / "b_rolled.mp4"
    temp_srt = outputs_folder / "temp.srt"
    subtitles_file = outputs_folder / "subtitles.srt"
    sentences_file = outputs_folder / "sentences.srt"
    unprocessed_frames_folder = outputs_folder / "frames"
    audio = outputs_folder / "audio.wav"
    restored_images_folder = outputs_folder / "restored_imgs"

    vr_folder = base_path / "Wav2Lip"

    enhance_folder = base_path / "wav2lip-HD"
    wav2lipPath = enhance_folder / "Wav2Lip-master"
    gfpganPath = enhance_folder / "GFPGAN-master"

    whisper_folder = base_path / "whisper_timestamped"

    def get_b_rolls(self):
        return sorted([
            str(self.b_rolls_folder / f)
            for f in os.listdir(self.b_rolls_folder)
            if os.path.isfile(os.path.join(self.b_rolls_folder, f))
        ])

    def get_input_audios(self):
        return [
            str(self.inputs_folder / f)
            for f in os.listdir(self.inputs_folder)
            if os.path.isfile(os.path.join(self.inputs_folder, f))
            and f.endswith(".wav")
            # initial input audio, may be longer than 1 minute
            and not f.startswith("_")
        ]


status = Status()
paths = Paths()


def set_env(data: dict):
    with open(".env", "w") as file:
        file.writelines([f"{key}={value}\n" for key, value in data.items()])


def get_env():
    env_dict = {}
    with open(".env", "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
    return env_dict


def start_vps():
    # TODO:
    pass


def close_vps():
    # TODO:
    pass


def read_content():
    with open(paths.content_path, "r") as file:
        return json.load(file)


def restore_dirs():
    for dir in ["inputs", "outputs"]:
        try:
            # os.rmdir(dir)
            shutil.rmtree(dir)
        except:
            pass
        try:
            os.mkdir(dir)
        except:
            pass


if __name__ == "__main__":
    for b_roll in paths.get_input_audios():
        print(b_roll)
