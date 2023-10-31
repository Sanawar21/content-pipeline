import os
import subprocess
from utils import paths

# Step 1: Clone the Wav2Lip repository
subprocess.run(["git", "clone", "https://github.com/justinjohn0306/Wav2Lip"])
os.chdir(paths.base_path / "Wav2Lip")

# Step 2: Download pretrained models
subprocess.run(["wget", "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip.pth",
               "-O", "checkpoints/wav2lip.pth"])
subprocess.run(["wget", "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip_gan.pth",
               "-O", "checkpoints/wav2lip_gan.pth"])
subprocess.run(["wget", "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/resnet50.pth",
               "-O", "checkpoints/resnet50.pth"])
subprocess.run(["wget", "https://github.com/justinjohn0306/Wav2Lip/releases/download/models/mobilenet.pth",
               "-O", "checkpoints/mobilenet.pth"])

# Step 3: Install required packages
subprocess.run(
    ["pip3", "install", "https://raw.githubusercontent.com/AwaleSajil/ghc/master/ghc-1.0-py3-none-any.whl"])
subprocess.run(
    ["pip3", "install", "git+https://github.com/elliottzheng/batch-face.git@master"])
subprocess.run(["pip3", "install", "ffmpeg-python", "mediapip3e==0.8.11"])

os.chdir(paths.base_path)

# Step 4: Clone the wav2lip-HD repository
subprocess.run(["git", "clone", "https://github.com/indianajson/wav2lip-HD"])
basePath = str(paths.base_path / "wav2lip-HD")
os.chdir(basePath)
wav2lipFolderName = 'Wav2Lip-master'
gfpganFolderName = 'GFPGAN-master'
wav2lipPath = basePath + '/' + wav2lipFolderName
gfpganPath = basePath + '/' + gfpganFolderName

# Step 5: Download additional files
subprocess.run(["wget", "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth",
               "-O", f"{wav2lipPath}/face_detection/detection/sfd/s3fd.pth"])
subprocess.run(["gdown", "https://drive.google.com/uc?id=1fQtBSYEyuai9MjBOF8j7zZ4oQ9W2N64q",
               "--output", f"{wav2lipPath}/checkpoints/"])
subprocess.run(["wget", "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
               "-P", f"{gfpganFolderName}/experiments/pretrained_models"])

# Step 6: Install requirements
os.chdir(basePath)
subprocess.run(["pip3", "install", "-r", "requirements.txt"])
subprocess.run(["pip3", "install", "-U", "librosa==0.8.1"])
subprocess.run(["mkdir", "inputs"])

# Step 7: Setup GFPGAN
os.chdir(gfpganFolderName)
subprocess.run(["python3", "setup.py", "develop"])

# Step 8: Clone basicsr repository
subprocess.run(["git", "clone", "https://github.com/Sanawar21/basicsr.git"])

# Step 9: Install facexlib
os.chdir(basePath)
subprocess.run(["pip3", "install", "facexlib"])

# Step 10: Clone and configure whisper-timestamped
os.chdir("..")
subprocess.run(
    ["git", "clone", "https://github.com/linto-ai/whisper-timestamped"])
os.chdir("whisper-timestamped")
subprocess.run(["python3", "setup.py", "install"])
subprocess.run(["pip3", "install", "openai-whisper==20230124",
               "ffmpeg-python", "dtw-python", "moviepy", "fuzzywuzzy"])
os.chdir("..")
os.rename("whisper-timestamped", "whisper_timestamped")
with open("whisper_timestamped/__init__.py", "w") as file:
    pass


subprocess.run(["pip3", "install", "-r", "requirements.txt"])
os.chdir(paths.base_path)
