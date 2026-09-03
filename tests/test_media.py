import pytest
from alenia_porter.media import Media, Video, Audio, Image, Stream

def test_media_models_creation():
    stream = Stream(index=0, codec_type="video", codec_name="h264")
    media = Media(
        path="test.mp4",
        container="mp4",
        duration=10.0,
        size=1024,
        streams=[stream]
    )
    
    assert media.main_video is not None
    assert media.main_audio is None
    
    vid = Video(path="v.mp4", container="mp4", duration=1.0, size=10)
    assert isinstance(vid, Media)
