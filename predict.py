# Prediction interface for Cog ⚙️
# https://github.com/replicate/cog/blob/main/docs/python.md

from cog import BasePredictor, Input, Path
from app import generate
from src.utils import paths, restore_dirs, make_archive
from src.client import download_zip
import shutil
import os


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory to make running multiple predictions efficient"""

    def predict(
        self,
        session_id: str = Input(
            default=None, description="Required if input video and audio not provided"),
        input_video: Path = Input(
            default=None, description="Input video (required if session ID not provided)"),
        input_audio: Path = Input(
            description="Input audio (wav only) for voice cloning (optional; can also be provided via the session ID)", default=None),
        voice_name: str = Input(description="Voice name (required)"),
        description: str = Input(
            description="Voice description (optional)", default=None),
        video_topic: str = Input(description="Video topic (required)"),
        content_type: str = Input(description="Type of content (required)"),
        key_points: str = Input(description="Key points (required)"),
    ) -> Path:
        """Run a single prediction on the model"""

        restore_dirs()

        if session_id == None:
            shutil.copy(input_video, paths.input_video)
            if input_audio is not None:
                shutil.copy(input_audio, paths.input_audio)
        else:
            download_zip(session_id)

        workflow = {
            'VideoTopic': video_topic,
            'TypeOfContent': content_type,
            'KeyPoints': key_points,
        }

        generate(voice_name, description, workflow)
        return Path("".join([str(paths.captioned_video).split(".")[0], "_with_audio.mp4"]))
