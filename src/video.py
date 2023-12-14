import subprocess
import cv2
import os
from tqdm import tqdm
from .utils import paths
from moviepy.editor import VideoFileClip, AudioFileClip

FPS = 30


def __change_fps(input_video_path=str(paths.output_video), output_video_path=str(paths.output_video), new_fps=FPS):
    video_capture = cv2.VideoCapture(input_video_path)
    current_fps = video_capture.get(cv2.CAP_PROP_FPS)

    if input_video_path == output_video_path:
        new_input_video_path = "".join(
            [input_video_path.split(".")[0], "_.mp4"])
        os.rename(input_video_path, new_input_video_path)
    else:
        new_input_video_path = input_video_path

    os.system(
        f"ffmpeg -i {new_input_video_path} -filter:v fps={new_fps} {output_video_path} -y")

    print(
        f"Video converted successfully from {current_fps} FPS to {new_fps} FPS.")


def preprocess():
    unprocessed = VideoFileClip(str(paths.input_video))
    trimmed = unprocessed.subclip(2, -2)
    reduced = trimmed.set_fps(FPS)
    reduced.write_videofile(str(paths.preprocessed_video), codec="libx264")


def generate_video():
    os.chdir(paths.vr_folder)
    output_file_path = paths.output_video

    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    pad_top = 0
    pad_bottom = 10
    pad_left = 0
    pad_right = 0
    rescaleFactor = 1
    nosmooth = True

    use_hd_model = False
    # use_hd_model = True  # test for better quality
    checkpoint_path = 'checkpoints/wav2lip.pth' if not use_hd_model else 'checkpoints/wav2lip_gan.pth'

    command = [
        'python',
        'inference.py',
        '--checkpoint_path',
        checkpoint_path,
        '--face',
        str(paths.input_video),
        '--audio',
        str(paths.audio),
        '--pads',
        str(pad_top),
        str(pad_bottom),
        str(pad_left),
        str(pad_right),
        '--resize_factor',
        str(rescaleFactor),
        '--outfile',
        str(paths.output_video)
    ]

    if not nosmooth:
        command.append('--nosmooth')

    result = subprocess.run(command, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)

    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    if result.returncode == 0:
        print("Command executed successfully.")
    else:
        print(f"Command failed with return code {result.returncode}.")
    os.chdir(paths.base_path)


def enhance_video():
    global FPS
    outputPath = str(paths.outputs_folder)
    inputVideoPath = str(paths.output_video)
    unProcessedFramesFolderPath = str(paths.unprocessed_frames_folder)
    gfpganFolderName = str(paths.enhance_folder / "GFPGAN-master")

    if not os.path.exists(unProcessedFramesFolderPath):
        os.makedirs(unProcessedFramesFolderPath)

    __change_fps()

    vidcap = cv2.VideoCapture(inputVideoPath)
    numberOfFrames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("New FPS: ", vidcap.get(cv2.CAP_PROP_FPS), "Frames: ", numberOfFrames)

    for frameNumber in tqdm(range(numberOfFrames)):
        _, image = vidcap.read()
        cv2.imwrite(
            os.path.join(
                unProcessedFramesFolderPath, str(frameNumber).zfill(4) + ".jpg"
            ),
            image,
        )

    command = f"cd {gfpganFolderName} && python inference_gfpgan.py -i {unProcessedFramesFolderPath} -o {outputPath} -v 1.3 -s 2 --only_center_face --bg_upsampler None"

    # Run the command
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}: {e.stderr}")
    images_to_video()


def images_to_video():
    fps = FPS if FPS is not None else 25
    image_files = sorted(
        [
            f
            for f in os.listdir(paths.restored_images_folder)
            if f.endswith((".jpg", ".png", ".jpeg", ".gif"))
        ]
    )

    if not image_files:
        raise ValueError("No image files found in the specified folder.")

    frame = cv2.imread(os.path.join(
        paths.restored_images_folder, image_files[0]))
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(str(paths.enhanced_video),
                            fourcc, fps, (width, height))

    for image_file in image_files:
        image_path = os.path.join(paths.restored_images_folder, image_file)
        frame = cv2.imread(image_path)
        video.write(frame)

    video.release()
    cv2.destroyAllWindows()


def merge_audio_and_video(video):

    video_clip = video
    audio_clip = AudioFileClip(str(paths.audio))

    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(
        "".join([str(paths.captioned_video).split(".")[0], "_with_audio.mp4"]), threads=8,  codec="libx264")

    video_clip.close()
    audio_clip.close()


if __name__ == "__main__":
    merge_audio_and_video()