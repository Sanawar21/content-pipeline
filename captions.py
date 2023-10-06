from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from fuzzywuzzy import fuzz, process
from utils import paths
import os
from whisper_timestamped import whisper_timestamped as whisper


def __convert_to_srt(result, output_file):
    srt = ""
    id = 1
    for segment in result["segments"]:
        for word in segment["words"]:
            word_id = id
            start_time = int(word["start"] * 1000)  # Convert to milliseconds
            end_time = int(word["end"] * 1000)  # Convert to milliseconds
            text = word["text"]
            id += 1

            srt += f"{word_id}\n"
            srt += f"{__milliseconds_to_srt_time(start_time)} --> {__milliseconds_to_srt_time(end_time)}\n"
            srt += f"{text}\n\n"

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(srt)
    return srt


def __convert_to_sentence_srt(result, output_file):
    sentence_data = []
    for segment in result["segments"]:
        sentence_data.append({
            "sentence": segment["text"],
            "start": segment["start"],
            "end": segment["end"],
        })
    with open(output_file, 'w') as srt_file:
        for i, item in enumerate(sentence_data, start=1):
            start_time = int(item['start'] * 1000)
            end_time = int(item['end'] * 1000)
            sentence = item['sentence']

            srt_file.write(f'{i}\n')
            srt_file.write(
                f'{__milliseconds_to_srt_time(start_time)} --> {__milliseconds_to_srt_time(end_time)}\n')
            srt_file.write(f'{sentence}\n')
            srt_file.write('\n')


def __milliseconds_to_srt_time(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def generate_srt():
    audio = whisper.load_audio(str(paths.audio))
    model = whisper.load_model("tiny")
    result = whisper.transcribe(model, audio, language="en")
    __convert_to_srt(result, str(paths.subtitles_file))
    __convert_to_sentence_srt(result, str(paths.sentences_file))


def __create_subtitles_clip(
    srt_file=str(paths.subtitles_file),
    video_file=str(paths.b_rolled_video),
    font="Ebrima-Bold",
    fontsize=200,
    color="white",
    method="caption",
    align="center",
    stroke_color=None,
    stroke_width=None,
):
    def generator(txt): return TextClip(
        txt,
        font=font,
        fontsize=fontsize,
        color=color,
        method=method,
        align=align,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
    )

    sub = SubtitlesClip(srt_file, generator)
    video_w, video_h = VideoFileClip(video_file).size
    sub.size = (video_w, video_h)
    # return sub.set_position(("center", "bottom"))
    return sub.set_position(("center", 0.8), relative=True)


def __add_subtitles_to_video(subtitles_clip):
    video_path = str(paths.b_rolled_video)
    global video_w, video_h
    video_clip = VideoFileClip(video_path)
    video_w, video_h = video_clip.size

    final_clip = CompositeVideoClip([video_clip, subtitles_clip])
    return final_clip.set_duration(video_clip.duration)


def add_to_video():
    os.chdir(paths.whisper_folder)
    generate_srt()
    subtitles_clip = __create_subtitles_clip()
    final_clip = __add_subtitles_to_video(subtitles_clip)
    final_clip.write_videofile(str(paths.captioned_video), fps=final_clip.fps)
    os.chdir(paths.base_path)


if __name__ == "__main__":
    add_to_video()
