"""
Capability models — data structures for the conversion capability engine.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TargetDefinition:
    """
    Explicit product-level description of a conversion target (§11).
    Replaces the simplistic KNOWN_VIDEO / KNOWN_AUDIO / KNOWN_IMAGE lists.
    """
    id: str
    display_name: str
    extensions: List[str]
    kind: str                        # 'video' | 'audio' | 'image' | 'animated_image'
    muxer: str
    level: int = 1                   # 1: Recommended, 2: Compatible
    supports_alpha: bool = True      # Does this target support transparency?
    video_encoders: List[str] = field(default_factory=list)
    audio_encoders: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


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
    warnings: List[str] = field(default_factory=list)
    required_streams: List[str] = field(default_factory=list)
    forbidden_streams: List[str] = field(default_factory=list)
    required_encoders: List[str] = field(default_factory=list)
    required_muxer: str = ""
    compatibility_rules: List[str] = field(default_factory=list)
