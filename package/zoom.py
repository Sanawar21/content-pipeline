from moviepy.video.fx.all import crop
from moviepy.editor import VideoFileClip, concatenate_videoclips
from .utils import paths


def __zoom(clip, percentage):
    new_clip = crop(clip, x_center=clip.w/2, y_center=clip.h/2,
                    width=clip.w * percentage, height=clip.h * percentage)
    width_scale = clip.w / new_clip.w
    height_scale = clip.h / new_clip.h

    scale_factor = min(width_scale, height_scale)

    new_clip = new_clip.resize(width=int(
        new_clip.w * scale_factor), height=int(new_clip.h * scale_factor))

    new_clip = new_clip.set_position(('center', 'center'))

    return new_clip


def __split_into_intervals(clip, zoom_intervals):

    def add_intervals():
        intervals = zoom_intervals
        duration = clip.duration
        if not intervals:
            return [(0, duration)]

        result = []
        for i, (start, end) in enumerate(intervals):
            if i == 0 and start > 0:
                result.append((0, start))
            result.append((start, end))

            if i < len(intervals) - 1:
                next_start, _ = intervals[i + 1]
                if end < next_start:
                    result.append((end, next_start))

        if intervals[-1][1] < duration:
            result.append((intervals[-1][1], duration))

        return result

    intervals = add_intervals()
    subclips = []
    for start_time, end_time in intervals:
        subclips.append(clip.subclip(start_time, end_time))
    return (subclips, intervals)


def __generate_intervals(duration: int):
    section_length = 6
    if section_length <= 0:
        return []
    sections = []
    start = 0
    while start < duration:
        end = start + section_length
        if end > duration:
            end = duration
        sections.append((start, end))
        start = end
    return [interval for interval in sections[1:-1:2] if (interval[1] - interval[0] > 0)]


def zoom_video_at_intervals(percentage=0.8):
    clips = []
    input_path = str(paths.enhanced_video)
    video = VideoFileClip(input_path)
    zoom_intervals = __generate_intervals(video.duration)
    interval_clips, all_intervals = __split_into_intervals(
        video, zoom_intervals)
    for i in range(len(interval_clips)):
        if all_intervals[i] in zoom_intervals:
            zoomed = __zoom(interval_clips[i], percentage)
            clips.append(zoomed)
        else:
            clips.append(interval_clips[i])

    return concatenate_videoclips(clips, method="compose")


if __name__ == "__main__":
    percentage = 0.8
    video_path = 'enhanced.mp4'
    output_path = 'zoomed.mp4'
    zoom_video_at_intervals()
