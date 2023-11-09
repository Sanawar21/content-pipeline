# Prediction interface for Cog ⚙️
# https://github.com/replicate/cog/blob/main/docs/python.md

from cog import BasePredictor, Input, Path
from app import generate
from utils import paths
import shutil
import subprocess


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory to make running multiple predictions efficient"""
        # self.model = torch.load("./weights.pth")

    def predict(
        self,
        input_video: Path = Input(description="Input video"),
        input_audio: Path = Input(
            description="Input audio (wav only) for voice cloning (optional)", default=None),
        voice_name: str = Input(description="Voice name"),
        description: str = Input(
            description="Voice description (optional)", default=None),
        video_topic: str = Input(description="Video topic"),
        content_type: str = Input(description="Type of content"),
        key_points: str = Input(description="Key points"),
    ) -> Path:
        """Run a single prediction on the model"""

        shutil.copy(input_video, paths.input_video)

        if input_audio is not None:
            shutil.copy(input_audio, paths.input_audio)

        workflow = {
            'VideoTopic': video_topic,
            'TypeOfContent': content_type,
            'KeyPoints': key_points,
        }

        generate(voice_name, description, workflow)
        return Path("".join([str(paths.captioned_video).split(".")[0], "_with_audio.mp4"]))
