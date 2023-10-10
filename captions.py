from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from fuzzywuzzy import fuzz, process
from whisper_timestamped import whisper_timestamped as whisper
from utils import paths
import os
import re


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


def __srt_to_dict(srt_file):
    srt_dict = []
    with open(srt_file, 'r', encoding='utf-8') as file:
        srt_data = file.read()

    # Split the SRT data into individual subtitle blocks
    subtitle_blocks = re.split(r'\n\s*\n', srt_data.strip())

    for block in subtitle_blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            index = int(lines[0])
            time_strs = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
            start_time_str, end_time_str = time_strs[:2]

            # Convert time strings to seconds
            start_time = sum(x * 60 ** i for i, x in enumerate(map(int,
                             reversed(start_time_str.replace(',', '').split(':'))))) / 1000.0
            end_time = sum(x * 60 ** i for i, x in enumerate(map(int,
                           reversed(end_time_str.replace(',', '').split(':'))))) / 1000.0

            sentence = '\n'.join(lines[2:])

            srt_dict.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'sentence': sentence
            })

    return srt_dict


def __dict_to_srt(srt_dict, output_file):
    srt_lines = []
    for item in srt_dict:
        srt_lines.append(str(item['index']))
        start_time = item['start_time']
        end_time = item['end_time']

        start_time_str = __format_time(start_time)
        end_time_str = __format_time(end_time)

        srt_lines.append(f"{start_time_str} --> {end_time_str}")
        srt_lines.append(item['sentence'])
        srt_lines.append('')

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write('\n'.join(srt_lines))


def __format_time(time_in_seconds):
    milliseconds = int((time_in_seconds - int(time_in_seconds)) * 1000)
    seconds = int(time_in_seconds) % 60
    minutes = int((time_in_seconds // 60) % 60)
    hours = int(time_in_seconds // 3600)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def __create_temp_srt():
    word_level = __srt_to_dict(str(paths.subtitles_file))
    sentence_level = __srt_to_dict(str(paths.sentences_file))
    temp_srt = []
    index = 0
    for sentence in sentence_level:
        time_range = (sentence["start_time"], sentence["end_time"])
        words = []
        for word in word_level:
            if word["start_time"] >= time_range[0] and word["end_time"] <= time_range[1]:
                words.append(word)

        for i in range(0, len(words), 3):
            three_words = words[i:i+3]
            start_time = three_words[0]["start_time"]
            end_time = three_words[-1]["end_time"]
            string = " ".join([word["sentence"] for word in three_words])
            temp_srt.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'sentence': string
            })
            index += 1

    __dict_to_srt(temp_srt, paths.temp_srt)


def generate_srt():
    audio = whisper.load_audio(str(paths.audio))
    model = whisper.load_model("tiny")
    result = whisper.transcribe(model, audio, language="en")
    __convert_to_srt(result, str(paths.subtitles_file))
    __convert_to_sentence_srt(result, str(paths.sentences_file))


def __create_subtitles_clip(
    video_file=str(paths.b_rolled_video),
    font="AppleTea",
    fontsize=75,
    color="white",
    method="label",
    align="center",
    stroke_color="black",
    stroke_width=7,
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

    __create_temp_srt()
    srt_file = str(paths.temp_srt)
    sub = SubtitlesClip(srt_file, generator)
    sub.size = VideoFileClip(video_file).size
    os.remove(paths.temp_srt)
    return sub.set_position(("center", 0.70), relative=True)


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
