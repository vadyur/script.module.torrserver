from typing import List, TypedDict


class PlayableItem(TypedDict):
    index: int
    name: str
    size: int


class FileItem(TypedDict):
    file_id: int
    path: str
    size: int


class FFProbeDisposition(TypedDict, total=False):
    default: int
    dub: int
    original: int
    comment: int
    lyrics: int
    karaoke: int
    forced: int
    hearing_impaired: int
    visual_impaired: int
    clean_effects: int
    attached_pic: int


class FFProbeStreamTags(TypedDict, total=False):
    language: str
    title: str
    BPS: str
    DURATION: str
    NUMBER_OF_BYTES: str
    NUMBER_OF_FRAMES: str
    _STATISTICS_TAGS: str
    _STATISTICS_WRITING_APP: str


class FFProbeStream(TypedDict, total=False):
    index: int
    id: str
    codec_name: str
    codec_long_name: str
    codec_type: str
    codec_time_base: str
    codec_tag_string: str
    codec_tag: str
    r_frame_rate: str
    avg_frame_rate: str
    time_base: str
    start_pts: int
    start_time: str
    duration_ts: int
    duration: str
    bit_rate: str
    bits_per_raw_sample: str
    nb_frames: str
    disposition: FFProbeDisposition
    tags: FFProbeStreamTags
    field_order: str
    profile: str
    width: int
    height: int
    has_b_frames: int
    sample_aspect_ratio: str
    display_aspect_ratio: str
    pix_fmt: str
    level: int
    sample_fmt: str
    sample_rate: str
    channels: int
    channel_layout: str


class FFProbeFormatTags(TypedDict, total=False):
    encoder: str


class FFProbeFormat(TypedDict, total=False):
    filename: str
    nb_streams: int
    nb_programs: int
    format_name: str
    format_long_name: str
    start_time: str
    duration: str
    size: str
    bit_rate: str
    probe_score: int
    tags: FFProbeFormatTags


class FFProbeChapterTags(TypedDict, total=False):
    title: str


class FFProbeChapter(TypedDict, total=False):
    id: int
    time_base: str
    start_time: str
    end_time: str
    tags: FFProbeChapterTags


class FFProbeResult(TypedDict, total=False):
    streams: List[FFProbeStream]
    format: FFProbeFormat
    chapters: List[FFProbeChapter]
