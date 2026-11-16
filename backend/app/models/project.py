from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

def get_utc_now():
    return datetime.now(timezone.utc)

class ProjectBase(SQLModel):
    name: str
    original_filename: str
    video_path: str
    duration: Optional[float] = 0.0
    width: Optional[int] = 0
    height: Optional[int] = 0
    fps: Optional[float] = 0.0
    status: str = "draft"  # draft, transcribing, ready, error

class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    subtitles: List["SubtitleSegment"] = Relationship(back_populates="project", cascade_delete=True)

class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ProjectCreate(SQLModel):
    name: Optional[str] = None

