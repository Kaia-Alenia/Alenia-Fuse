"""
Capability models — data structures for the conversion capability engine.
"""
from dataclasses import dataclass, field


@dataclass
class TargetDefinition:
    """
    Explicit product-level description of a conversion target (§11).
    Replaces the simplistic KNOWN_VIDEO / KNOWN_AUDIO / KNOWN_IMAGE lists.
    """
    id: str
    display_name: str
    extensions: list[str]
    kind: str                        # 'video' | 'audio' | 'image' | 'animated_image'
    muxer: str
    level: int = 1                   # 1: Recommended, 2: Compatible
    supports_alpha: bool = True      # Does this target support transparency?
    video_encoders: list[str] = field(default_factory=list)
    audio_encoders: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class ConversionCapability:
    """
    Result of evaluating whether a specific source -> target conversion is
    possible with the bundled FFmpeg (§9).
    """
    source_media_kind: str           # 'video' | 'audio' | 'image' | 'animated_image'
    target_id: str
    target_extension: str
    target_kind: str
    available: bool
    reason: str                      # human-readable explanation if not available
    level: int = 1
    warnings: list[str] = field(default_factory=list)
    required_streams: list[str] = field(default_factory=list)
    forbidden_streams: list[str] = field(default_factory=list)
    required_encoders: list[str] = field(default_factory=list)
    required_muxer: str = ""
    compatibility_rules: list[str] = field(default_factory=list)
