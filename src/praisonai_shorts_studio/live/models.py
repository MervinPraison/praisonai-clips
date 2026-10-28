"""Stable clip identity and validated framing values."""
from dataclasses import asdict, dataclass
from .lua import lua_number

# One mapping for native readback, validation, SDK edits and restoration.
FRAMING_KEYS = {
    "zoom_x": "ZoomX", "zoom_y": "ZoomY", "pan": "Pan", "tilt": "Tilt",
    "crop_left": "CropLeft", "crop_right": "CropRight",
    "crop_top": "CropTop", "crop_bottom": "CropBottom",
}


def framing_changes(changes: dict) -> dict:
    if not changes or changes.keys() - FRAMING_KEYS.keys():
        raise ValueError("Provide framing fields: " + ", ".join(FRAMING_KEYS))
    for name, value in changes.items():
        lua_number(value)
        if name.startswith("zoom_") and value <= 0:
            raise ValueError("Zoom must be positive")
        if name.startswith("crop_") and value < 0:
            raise ValueError("Crop edges cannot be negative")
    return {FRAMING_KEYS[key]: value for key, value in changes.items()}


@dataclass(frozen=True)
class ClipTarget:
    """Identity captured from get_timeline_items; indices alone are insufficient."""
    project_id: str
    timeline_id: str
    clip_id: str
    track_index: int
    clip_index: int

    def __post_init__(self):
        for name in ("project_id", "timeline_id", "clip_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        for name in ("track_index", "clip_index"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class Framing:
    zoom_x: float = 1
    zoom_y: float = 1
    pan: float = 0
    tilt: float = 0
    crop_left: float = 0
    crop_right: float = 0
    crop_top: float = 0
    crop_bottom: float = 0

    def __post_init__(self):
        framing_changes(asdict(self))

    @classmethod
    def from_properties(cls, properties: dict):
        return cls(**{key: properties[native] for key, native in FRAMING_KEYS.items()})

    def to_dict(self) -> dict:
        return asdict(self)
