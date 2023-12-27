from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from src.utils import status, start_vps, close_vps, restore_dirs, paths
from src import audio, video, captions, zoom, b_rolls, content
import os


app = Flask(__name__)

INPUT_FOLDER = "inputs"
app.config["INPUT_FOLDER"] = INPUT_FOLDER

OUTPUT_FOLDER = "outputs"
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


@app.route("/api/get_status", methods=["GET"])
def get_status():
    return status.now


@app.route("/api/generate_video", methods=["POST"])
def generate_video():
    voice = request.form.get('voice')
    description = request.form.get('description')
    workflow = {
        'VideoTopic': request.form.get('video_topic'),
        'TypeOfContent': request.form.get('content_type'),
        'KeyPoints': request.form.get('keypoints')
    }
    return generate(voice, description, workflow)


@app.route("/api/get_video", methods=["GET"])
def get_video():
    return send_file("".join([str(paths.captioned_video).split(".")[0], "_with_audio.mp4"]))


@app.route("/api/start_session", methods=["POST"])
def start_session():
    if status.now != status.off:
        return

    start_vps()
    restore_dirs()

    files = request.files.getlist("files")

    if not files:
        return jsonify({"message": "No files uploaded"}), 400

    wav_file_number = 1
    for file in files:
        if file.filename == "":
            continue

        filename = secure_filename(file.filename)
        if filename.endswith(".wav"):
            filename = f"audio{str(wav_file_number).zfill(4)}.wav"
            wav_file_number += 1
        elif filename.endswith(".mp4"):
            filename = "video.mp4"
        elif filename.endswith(".txt"):
            filename = "script.txt"

        file_path = os.path.join(app.config["INPUT_FOLDER"], filename)
        file.save(file_path)

    status.set(status.free)


@app.route("/api/end_session", methods=["POST"])
def end_session():
    if status.now == status.off:
        return

    restore_dirs()
    status.set(status.off)
    close_vps()


def generate(voice, description, workflow):
    # try:
    content.process_workflow(workflow)
    status.set(status.generating_audio)
    if voice not in audio.list_voices().keys():
        audio.clone(voice, description)

    audio.generate(voice)
    captions.generate_srt()
    status.set(status.generating_lipsync)
    video.generate_video()
    status.set(status.enhancing_video)
    video.enhance_video()

    status.set(status.zooming_video)
    zoomed = zoom.zoom_video_at_intervals()
    status.set(status.adding_brolls)
    b_rolled = b_rolls.add_b_rolls(zoomed)
    # status.set(status.generating_subtitles)
    # captioned = captions.add_to_video(b_rolled)
    # status.set(status.combining_audio_video)
    # video.merge_audio_and_video(video=captioned)
    video.merge_audio_and_video(video=b_rolled)
    status.set(status.done)
    return status.done
    # except Exception as e:
    #     return e
