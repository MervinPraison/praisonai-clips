from __future__ import annotations

import math
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Word(BaseModel):
    word: str
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start or not self.word.strip():
            raise ValueError("Word must have text and nonnegative, measured duration")
        return self


class Subject(BaseModel):
    description: str
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)


class Scene(BaseModel):
    time: float
    scene: str
    actions: str
    screen_content: str
    visible_text: str
    subjects: list[Subject]
    confidence: float = Field(ge=0, le=1)


class SceneBatch(BaseModel):
    scenes: list[Scene]


class Candidate(BaseModel):
    start_word: int = Field(ge=0)
    end_word: int = Field(ge=0)
    title: str
    rationale: str
    score: float = Field(ge=0, le=1)


class Selection(BaseModel):
    clips: list[Candidate]


class Mapping(BaseModel):
    source_start: float = Field(ge=0, allow_inf_nan=False)
    source_end: float = Field(gt=0, allow_inf_nan=False)
    output_start: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered(self):
        if self.source_end <= self.source_start:
            raise ValueError("Empty or reversed edit")
        return self

    @property
    def output_end(self):
        return self.output_start + self.source_end - self.source_start


class EDL(BaseModel):
    version: int = 1
    title: str
    rationale: str
    mappings: list[Mapping]
    mode: str = "fit"
    crop_x: float = 0.5
    crop_y: float = 0.5
    crop_evidence: str = ""

    @model_validator(mode="after")
    def valid(self):
        if self.mode not in {"fit", "crop"}:
            raise ValueError("Unknown framing mode")
        if not self.mappings:
            raise ValueError("An edit needs at least one mapping")
        cursor = 0.0
        for m in self.mappings:
            if abs(m.output_start - cursor) > 1e-6:
                raise ValueError("Output timeline must be contiguous and start at zero")
            cursor = m.output_end
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in (self.crop_x, self.crop_y)):
            raise ValueError("Crop centers must be normalized")
        return self

    @property
    def duration(self):
        return self.mappings[-1].output_end


class CropChoice(BaseModel):
    mode: Literal["crop", "fit"]
    center_x: float = Field(ge=0, le=1)
    center_y: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    reason: str


class Review(BaseModel):
    accepted: bool
    confidence: float = Field(ge=0, le=1)
    defects: list[str]
    repair: Literal["fit", "none"]


class MomentChoice(BaseModel):
    option_id: int = Field(ge=0)
    title: str
    rationale: str
    score: float = Field(ge=0, le=1)


class RankedSelection(BaseModel):
    clips: list[MomentChoice]
