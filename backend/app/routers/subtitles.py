import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import get_session
from app.models.subtitle import SubtitleSegment, SubtitleSegmentRead, SubtitleSegmentUpdate
from app.services.subtitle_formatter import resegment_by_words_or_chars, sync_words_with_text

router = APIRouter(prefix="/api/subtitles", tags=["subtitles"])

class ResegmentRequest(BaseModel):
    max_words: int = 4
    max_chars: int = 30

class SplitRequest(BaseModel):
    subtitle_id: int
    split_time: float
    text_part1: str
    text_part2: str

class MergeRequest(BaseModel):
    subtitle_id_1: int
    subtitle_id_2: int

class ReorderRequest(BaseModel):
    subtitle_ids: List[int]

class SwapRequest(BaseModel):
    subtitle_id_1: int
    subtitle_id_2: int

class TimeShiftRequest(BaseModel):
    offset_seconds: float

@router.get("/{project_id}", response_model=List[SubtitleSegmentRead])
def get_project_subtitles(project_id: int, session: Session = Depends(get_session)):
    subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc())
    ).all()

    result = []
    for s in subs:
        result.append(SubtitleSegmentRead(
            id=s.id,
            project_id=s.project_id,
            sequence=s.sequence,
            start_time=s.start_time,
            end_time=s.end_time,
            text=s.text,
            words_json=s.words_json,
            words=s.words
        ))
    return result

@router.put("/{subtitle_id}", response_model=SubtitleSegmentRead)
def update_subtitle(
    subtitle_id: int,
    data: SubtitleSegmentUpdate,
    session: Session = Depends(get_session)
):
    sub = session.get(SubtitleSegment, subtitle_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subtitle tidak ditemukan")

    text_or_time_changed = False

    if data.text is not None and data.text.strip() != sub.text:
        sub.text = data.text.strip()
        text_or_time_changed = True
    if data.start_time is not None and round(data.start_time, 3) != sub.start_time:
        sub.start_time = round(data.start_time, 3)
        text_or_time_changed = True
    if data.end_time is not None and round(data.end_time, 3) != sub.end_time:
        sub.end_time = round(data.end_time, 3)
        text_or_time_changed = True
    if data.sequence is not None:
        sub.sequence = data.sequence

    if text_or_time_changed or not sub.words_json:
        # Keep word-level timestamps strictly synchronized with the edited text
        synced_words = sync_words_with_text(sub.text, sub.words, sub.start_time, sub.end_time)
        sub.set_words(synced_words)

    session.add(sub)
    session.commit()
    session.refresh(sub)
    return SubtitleSegmentRead(
        id=sub.id,
        project_id=sub.project_id,
        sequence=sub.sequence,
        start_time=sub.start_time,
        end_time=sub.end_time,
        text=sub.text,
        words_json=sub.words_json,
        words=sub.words
    )

@router.post("/{project_id}", response_model=SubtitleSegmentRead)
def create_subtitle(
    project_id: int,
    start_time: float,
    end_time: float,
    text: str,
    insert_after_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    clean_text = text.strip() or "Teks subtitle baru"
    clean_start = round(start_time, 3)
    clean_end = round(end_time, 3)
    if clean_end <= clean_start:
        clean_end = round(clean_start + 2.0, 3)

    existing_subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc())
    ).all()

    target_seq = None
    if insert_after_id:
        for s in existing_subs:
            if s.id == insert_after_id:
                target_seq = s.sequence + 1
                break

    if target_seq is None:
        # Smart chronological placement based on start_time
        target_seq = 1
        for s in existing_subs:
            if s.start_time <= clean_start:
                target_seq = s.sequence + 1
            else:
                break

    # Shift all subtitles at or after target_seq
    for s in existing_subs:
        if s.sequence >= target_seq:
            s.sequence += 1
            session.add(s)

    new_sub = SubtitleSegment(
        project_id=project_id,
        sequence=target_seq,
        start_time=clean_start,
        end_time=clean_end,
        text=clean_text
    )
    new_words = sync_words_with_text(clean_text, [], clean_start, clean_end)
    new_sub.set_words(new_words)

    session.add(new_sub)
    session.commit()

    # Re-normalize sequences to guarantee 1..N strictly
    all_subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc(), SubtitleSegment.start_time.asc())
    ).all()
    for idx, s in enumerate(all_subs, start=1):
        if s.sequence != idx:
            s.sequence = idx
            session.add(s)
    session.commit()
    session.refresh(new_sub)

    return SubtitleSegmentRead(
        id=new_sub.id,
        project_id=new_sub.project_id,
        sequence=new_sub.sequence,
        start_time=new_sub.start_time,
        end_time=new_sub.end_time,
        text=new_sub.text,
        words_json=new_sub.words_json,
        words=new_sub.words
    )

@router.post("/{project_id}/reorder")
def reorder_subtitles(
    project_id: int,
    req: ReorderRequest,
    session: Session = Depends(get_session)
):
    subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
    ).all()
    sub_map = {s.id: s for s in subs}
    for idx, sid in enumerate(req.subtitle_ids, start=1):
        if sid in sub_map:
            sub_map[sid].sequence = idx
            session.add(sub_map[sid])
    session.commit()
    return {"message": "Urutan subtitle berhasil diperbarui"}

@router.post("/{project_id}/swap")
def swap_subtitles(
    project_id: int,
    req: SwapRequest,
    session: Session = Depends(get_session)
):
    sub1 = session.get(SubtitleSegment, req.subtitle_id_1)
    sub2 = session.get(SubtitleSegment, req.subtitle_id_2)
    if not sub1 or not sub2:
        raise HTTPException(status_code=404, detail="Subtitle tidak ditemukan")
    seq1, seq2 = sub1.sequence, sub2.sequence
    sub1.sequence = seq2
    sub2.sequence = seq1
    session.add(sub1)
    session.add(sub2)
    session.commit()
    return {"message": "Posisi subtitle berhasil ditukar"}

@router.post("/{project_id}/sort-by-time", response_model=List[SubtitleSegmentRead])
def sort_subtitles_by_time(
    project_id: int,
    session: Session = Depends(get_session)
):
    subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.start_time.asc())
    ).all()
    for idx, s in enumerate(subs, start=1):
        s.sequence = idx
        session.add(s)
    session.commit()
    return [
        SubtitleSegmentRead(
            id=s.id,
            project_id=s.project_id,
            sequence=s.sequence,
            start_time=s.start_time,
            end_time=s.end_time,
            text=s.text,
            words_json=s.words_json,
            words=s.words
        )
        for s in subs
    ]

@router.post("/{project_id}/time-shift", response_model=List[SubtitleSegmentRead])
def time_shift_subtitles(
    project_id: int,
    req: TimeShiftRequest,
    session: Session = Depends(get_session)
):
    """
    Shifts the start and end times of all subtitles in the project by offset_seconds.
    Also shifts all word-level timestamps proportionally and prevents negative timestamps.
    """
    subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc())
    ).all()

    offset = round(req.offset_seconds, 3)
    result = []

    for s in subs:
        new_start = max(0.0, round(s.start_time + offset, 3))
        new_end = max(round(new_start + 0.1, 3), round(s.end_time + offset, 3))

        s.start_time = new_start
        s.end_time = new_end

        # Shift word timestamps
        words = s.words
        if words:
            shifted_words = []
            for w in words:
                w_start = max(0.0, round(float(w.get("start", new_start)) + offset, 3))
                w_end = max(round(w_start + 0.03, 3), round(float(w.get("end", new_end)) + offset, 3))
                shifted_words.append({
                    "word": w.get("word", ""),
                    "start": w_start,
                    "end": w_end,
                    "probability": w.get("probability", 1.0)
                })
            s.set_words(shifted_words)
        else:
            s.set_words(sync_words_with_text(s.text, [], s.start_time, s.end_time))

        session.add(s)
        result.append(s)

    session.commit()

    return [
        SubtitleSegmentRead(
            id=s.id,
            project_id=s.project_id,
            sequence=s.sequence,
            start_time=s.start_time,
            end_time=s.end_time,
            text=s.text,
            words_json=s.words_json,
            words=s.words
        )
        for s in result
    ]

@router.delete("/{subtitle_id}")
def delete_subtitle(subtitle_id: int, session: Session = Depends(get_session)):
    sub = session.get(SubtitleSegment, subtitle_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subtitle tidak ditemukan")

    project_id = sub.project_id
    session.delete(sub)
    session.commit()

    # Re-sequence remaining
    remaining = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc())
    ).all()
    for idx, s in enumerate(remaining, start=1):
        s.sequence = idx
        session.add(s)
    session.commit()

    return {"message": "Subtitle dihapus"}

@router.post("/{project_id}/split")
def split_subtitle(
    project_id: int,
    req: SplitRequest,
    session: Session = Depends(get_session)
):
    original = session.get(SubtitleSegment, req.subtitle_id)
    if not original:
        raise HTTPException(status_code=404, detail="Subtitle tidak ditemukan")

    orig_end = original.end_time
    split_t = round(req.split_time, 3)

    # Split original words based on split timestamp
    existing_words = original.words
    part1_words_raw = [w for w in existing_words if float(w.get("end", 0)) <= split_t]
    part2_words_raw = [w for w in existing_words if float(w.get("start", 0)) >= split_t]

    # Update original as part 1
    original.end_time = split_t
    original.text = req.text_part1.strip()
    original.set_words(sync_words_with_text(original.text, part1_words_raw, original.start_time, split_t))
    session.add(original)

    # Shift subsequent sequences by 1
    later_subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .where(SubtitleSegment.sequence > original.sequence)
    ).all()
    for ls in later_subs:
        ls.sequence += 1
        session.add(ls)

    # Create part 2
    part2 = SubtitleSegment(
        project_id=project_id,
        sequence=original.sequence + 1,
        start_time=split_t,
        end_time=orig_end,
        text=req.text_part2.strip()
    )
    part2.set_words(sync_words_with_text(part2.text, part2_words_raw, split_t, orig_end))
    session.add(part2)
    session.commit()

    return {"message": "Subtitle berhasil dipisah"}

@router.post("/{project_id}/merge")
def merge_subtitles(
    project_id: int,
    req: MergeRequest,
    session: Session = Depends(get_session)
):
    sub1 = session.get(SubtitleSegment, req.subtitle_id_1)
    sub2 = session.get(SubtitleSegment, req.subtitle_id_2)
    if not sub1 or not sub2:
        raise HTTPException(status_code=404, detail="Satu atau kedua subtitle tidak ditemukan")

    merged_start = min(sub1.start_time, sub2.start_time)
    merged_end = max(sub1.end_time, sub2.end_time)
    merged_text = f"{sub1.text} {sub2.text}".strip()

    sub1.start_time = merged_start
    sub1.end_time = merged_end
    sub1.text = merged_text
    
    # Merge and synchronize words
    merged_words = sync_words_with_text(merged_text, sub1.words + sub2.words, merged_start, merged_end)
    sub1.set_words(merged_words)
    session.add(sub1)

    session.delete(sub2)
    session.commit()

    # Re-sequence
    all_subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.start_time.asc())
    ).all()
    for idx, s in enumerate(all_subs, start=1):
        s.sequence = idx
        session.add(s)
    session.commit()

    return {"message": "Subtitle berhasil digabungkan"}

@router.post("/{project_id}/resegment")
def resegment_subtitles(
    project_id: int,
    req: ResegmentRequest,
    session: Session = Depends(get_session)
):
    """
    Auto re-segments the project subtitles according to max words/chars.
    Uses word-level timestamps when available.
    """
    subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc())
    ).all()

    if not subs:
        raise HTTPException(status_code=400, detail="Tidak ada subtitle untuk diatur ulang")

    raw_segments = []
    for s in subs:
        raw_segments.append({
            "sequence": s.sequence,
            "start": s.start_time,
            "end": s.end_time,
            "text": s.text,
            "words": s.words
        })

    new_segments = resegment_by_words_or_chars(
        raw_segments,
        max_words=req.max_words,
        max_chars=req.max_chars
    )

    # Delete existing
    for s in subs:
        session.delete(s)

    # Insert new
    for ns in new_segments:
        item = SubtitleSegment(
            project_id=project_id,
            sequence=ns["sequence"],
            start_time=ns["start"],
            end_time=ns["end"],
            text=ns["text"]
        )
        item.set_words(ns.get("words", []))
        session.add(item)

    session.commit()
    return {"message": "Re-segmentasi berhasil", "total": len(new_segments)}

