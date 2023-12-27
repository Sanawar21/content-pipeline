# Prediction interface for Cog ⚙️
# https://github.com/replicate/cog/blob/main/docs/python.md

from cog import BasePredictor, Input, Path
from app import generate
from src.utils import paths, restore_dirs, make_archive
import shutil


class Predictor(BasePredictor):
    def setup(self) -> None:
        """Load the model into memory to make running multiple predictions efficient"""

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

        restore_dirs()

        shutil.copy(input_video, paths.input_video)
        if input_audio is not None:
            shutil.copy(input_audio, paths.input_audio)
        workflow = {
            'VideoTopic': video_topic,
            'TypeOfContent': content_type,
            'KeyPoints': key_points,
        }

        generate(voice_name, description, workflow)
        # make_archive(paths.outputs_folder, paths.zip_file)
        return Path(str(paths.outputs_folder))
