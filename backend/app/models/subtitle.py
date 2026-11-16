import json
from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Relationship

class SubtitleSegmentBase(SQLModel):
    sequence: int
    start_time: float  # In seconds
    end_time: float    # In seconds
    text: str
    words_json: Optional[str] = None  # JSON string of word timestamps

class SubtitleSegment(SubtitleSegmentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)

    project: Optional["Project"] = Relationship(back_populates="subtitles")

    @property
    def words(self) -> List[dict]:
        if not self.words_json:
            return []
        try:
            return json.loads(self.words_json)
        except Exception:
            return []

    def set_words(self, words: List[dict]):
        self.words_json = json.dumps(words, ensure_ascii=False)

class SubtitleSegmentRead(SubtitleSegmentBase):
    id: int
    project_id: int
    words: Optional[List[dict]] = []

class SubtitleSegmentCreate(SubtitleSegmentBase):
    project_id: int

class SubtitleSegmentUpdate(SQLModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    text: Optional[str] = None
    sequence: Optional[int] = None
    words_json: Optional[str] = None

