from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from fuzzywuzzy import process
from .utils import paths, read_content
from .video import FPS
from dotenv import load_dotenv
import math
import requests
import random
import os
import shutil
import numpy as np

load_dotenv(paths.env_path)


class BRoll:

    def __init__(self, path: str, duration, start_time) -> None:
        self.path = path
        self.duration = duration
        self.start_time = start_time
        self.b_roll = self.__create_b_roll()

    def resize(self, main_clip_w, main_clip_h):
        b_roll_clip = self.b_roll
        width_scale = main_clip_w / b_roll_clip.w
        height_scale = main_clip_h / b_roll_clip.h

        scale_factor = min(width_scale, height_scale)

        b_roll_clip = b_roll_clip.resize(width=int(
            b_roll_clip.w * scale_factor), height=int(b_roll_clip.h * scale_factor))

        b_roll_clip = b_roll_clip.set_position(('center', 'center'))
        self.b_roll = b_roll_clip
        return self

    def __create_b_roll(self):

        if self.path.endswith((".jpg", ".png", "jpeg")):
            b_roll_clip = ImageClip(
                self.path, duration=self.duration).set_start(self.start_time)
            b_roll_clip.fps = FPS
        else:
            b_roll_clip = VideoFileClip(self.path).set_duration(
                self.duration).set_start(self.start_time)

        return b_roll_clip


def __create_black_image(resolution):
    width, height = resolution
    image = np.full((height, width, 3), (0, 0, 0), dtype=np.uint8)
    return image


def __resize_b_rolls(b_rolls: 'list[BRoll]', main_clip_w, main_clip_h):
    resized_b_rolls = []
    for b_roll in b_rolls:
        resized_b_rolls.append(b_roll.resize(main_clip_w, main_clip_h))
    return resized_b_rolls


def __blackout_sections(video, b_rolls: "list[BRoll]"):
    video_clip = video

    modified_sections = []
    last_end_time = 0

    for b_roll in b_rolls:
        start_time = b_roll.start_time
        end_time = b_roll.start_time + b_roll.duration
        if start_time > last_end_time:
            modified_sections.append(
                video_clip.subclip(last_end_time, start_time))

        blackout_duration = end_time - start_time
        black_frame_clip = ImageClip(
            __create_black_image(video_clip.size), duration=blackout_duration)
        black_frame_clip.size = video_clip.size
        modified_sections.append(black_frame_clip)

        last_end_time = end_time

    if last_end_time < video_clip.duration:
        modified_sections.append(video_clip.subclip(
            last_end_time, video_clip.duration))

    final_video = concatenate_videoclips(modified_sections, method="compose")

    return final_video


def __create_composite_video(base_video, b_roll_list: "list[BRoll]"):
    main_clip = base_video
    composite_clips = [main_clip]

    for b_roll_info in b_roll_list:
        b_roll_clip = b_roll_info.b_roll
        composite_clips.append(b_roll_clip.set_position('center'))

    final_composite = CompositeVideoClip(composite_clips)
    return final_composite


def __map_keywords_to_transcript(broll_data, transcript_data):
    result = []
    transcript_index = 0  # Keep track of the current transcript sentence

    for broll_item in broll_data:
        # Assuming each b-roll has only one keyword
        keyword = broll_item['keywords'][0]

        # Extract the sentence from the b-roll item
        broll_sentence = broll_item['sentence']

        # Find the best matching transcript sentence using fuzzywuzzy
        best_match, match_score = process.extractOne(
            broll_sentence, [t['sentence'] for t in transcript_data])

        best_match = transcript_data[[t['sentence']
                                      for t in transcript_data].index(best_match)]
        # Check for overlap and adjust the start time if needed
        while transcript_index < len(transcript_data) - 1:
            current_transcript = transcript_data[transcript_index]
            next_transcript = transcript_data[transcript_index + 1]

            current_end = current_transcript['start'] + \
                current_transcript['duration']
            next_start = next_transcript['start']

            if current_end > next_start:
                # There is an overlap, so increment the transcript_index
                transcript_index += 1
            else:
                # No overlap, break the loop
                break

        # Calculate the start and end times
        if transcript_index < len(transcript_data):
            start_time = max(
                best_match['start'], transcript_data[transcript_index]['start'])
        else:
            start_time = best_match['start']

        end_time = start_time + best_match['duration']

        # Append the result to the list
        result.append(
            {'keyword': keyword, 'start': start_time, 'end': end_time})

        # Increment the transcript index
        transcript_index += 1

    return result


def __get_and_write_image(word, count):

    url = "https://pexelsdimasv1.p.rapidapi.com/v1/search"

    querystring = {"query": word, "locale": "en-US",
                   "per_page": "15", "page": "1"}

    headers = {
        "Authorization": os.getenv("PEXELS"),
        "X-RapidAPI-Key": os.getenv("RAPIDAPI"),
        "X-RapidAPI-Host": "PexelsdimasV1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    images = list(response.json()["photos"])

    for i in range(count):
        image = random.choice(images)
        images.remove(image)
        with open(paths.b_rolls_folder / f"{word}_{str(i + 1).zfill(3)}.jpg", "wb") as file:
            file.write(requests.get(image["src"]["portrait"]).content)


def __generate_b_rolls() -> 'list[BRoll]':
    try:
        shutil.rmtree(paths.b_rolls_folder)
    except:
        pass

    try:
        os.mkdir(paths.b_rolls_folder)
    except:
        pass

    content = read_content()
    b_roll_data = content["b-roll"]
    keywords = []
    keywords_data = {}

    for broll in b_roll_data:
        keywords.extend(broll["keywords"])
    for keyword in keywords:
        if keyword not in keywords_data.keys():
            keywords_data[keyword] = keywords.count(keyword)
    for word, count in keywords_data.items():
        __get_and_write_image(word, count)

    srt_data = __parse_srt_file(paths.sentences_file)
    b_roll_paths = paths.get_b_rolls()
    results = __map_keywords_to_transcript(b_roll_data, srt_data)

    b_rolls = []
    counts = {}
    for i in range(len(results)):
        min_start = results[i]['start']
        max_end = results[i +
                          1]['start'] if i != len(results) - 1 else results[i]['end']
        keywords_to_fit = b_roll_data[i]["keywords"]
        max_possible = math.floor((max_end - min_start) / 3)

        if max_possible < len(keywords_to_fit):
            keywords_to_fit = keywords_to_fit[:max_possible]

        for keyword in keywords_to_fit:
            if keyword in counts.keys():
                counts[keyword] += 1
            else:
                counts[keyword] = 1
            path = [p for p in b_roll_paths if keyword in p][counts[keyword] - 1]
            duration = 1.5
            start_time = min_start + keywords_to_fit.index(keyword)
            min_start += 1.5
            b_roll = BRoll(path, duration, start_time)
            b_rolls.append(b_roll)

    return b_rolls


def __srt_time_to_seconds(srt_time):
    # Split the time into hours, minutes, seconds, and milliseconds
    time_parts = srt_time.split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])

    # Split the seconds and milliseconds
    seconds, milliseconds = map(
        int, time_parts[2].replace(',', '.').split('.'))

    # Calculate the total time in seconds
    total_seconds = (hours * 3600) + (minutes * 60) + \
        seconds + (milliseconds / 1000)

    return total_seconds


def __parse_srt_file(file_path):
    subtitles = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Initialize variables to store subtitle data
        sentence = ''
        start_time = ''
        duration = ''

        for line in lines:
            line = line.strip()

            # Check if the line is empty, indicating the end of a subtitle entry
            if not line:
                if sentence and start_time and duration:
                    subtitle_data = {
                        'sentence': sentence[sentence.index(" ")+1:],
                        'start': __srt_time_to_seconds(start_time),
                        'duration': __srt_time_to_seconds(duration) - __srt_time_to_seconds(start_time)
                    }
                    subtitles.append(subtitle_data)

                # Reset variables for the next subtitle entry
                sentence = ''
                start_time = ''
                duration = ''
            elif '-->' in line:
                # Extract start time and duration from the time format in SRT
                start_time, duration = line.split('-->')
                start_time = start_time.strip()
                duration = duration.strip()
            else:
                # Add the line to the current sentence
                sentence += line + ' '

    except FileNotFoundError:
        print(f"File not found: {file_path}")

    return subtitles


def add_b_rolls(video):
    b_rolls = __generate_b_rolls()
    main_clip = __blackout_sections(video, b_rolls)
    resized_b_rolls = __resize_b_rolls(b_rolls, main_clip.w, main_clip.h)
    return __create_composite_video(main_clip, resized_b_rolls)


if __name__ == "__main__":
    # add_b_rolls()
    pass
