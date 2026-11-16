import re
from typing import List, Dict, Any, Optional

def sync_words_with_text(
    text: str,
    existing_words: Optional[List[Dict[str, Any]]],
    start_time: float,
    end_time: float
) -> List[Dict[str, Any]]:
    """
    Synchronizes word-level timestamps with the segment text.
    - If the number of words matches the existing words (e.g. fixing a typo like 'tertama' -> 'pertama'),
      preserves exact start/end timestamps from the original audio alignment.
    - If word count differs or words are missing, smoothly distributes the time window [start_time, end_time]
      proportionally based on character lengths so CapCut animation stays natural and in-sync.
    - If segment start/end timings were shifted, proportionally scales the words into the new range.
    """
    tokens = text.strip().split()
    if not tokens:
        return []

    start_t = round(float(start_time), 3)
    end_t = round(float(end_time), 3)
    duration = max(0.05, end_t - start_t)

    # 1. Exact count match
    if existing_words and len(existing_words) == len(tokens):
        orig_min = float(existing_words[0].get("start", start_t))
        orig_max = float(existing_words[-1].get("end", end_t))
        orig_dur = max(0.05, orig_max - orig_min)

        needs_scaling = abs(orig_min - start_t) > 0.05 or abs(orig_max - end_t) > 0.05
        synced = []

        for i, tok in enumerate(tokens):
            w_orig = existing_words[i]
            w_s = float(w_orig.get("start", start_t))
            w_e = float(w_orig.get("end", end_t))

            if needs_scaling and orig_dur > 0:
                norm_s = max(0.0, min(1.0, (w_s - orig_min) / orig_dur))
                norm_e = max(0.0, min(1.0, (w_e - orig_min) / orig_dur))
                scaled_s = round(start_t + norm_s * duration, 3)
                scaled_e = round(start_t + norm_e * duration, 3)
                synced.append({
                    "word": tok,
                    "start": scaled_s,
                    "end": max(round(scaled_s + 0.03, 3), scaled_e),
                    "probability": float(w_orig.get("probability", 1.0))
                })
            else:
                synced.append({
                    "word": tok,
                    "start": round(w_s, 3),
                    "end": max(round(w_s + 0.03, 3), round(w_e, 3)),
                    "probability": float(w_orig.get("probability", 1.0))
                })

        if synced:
            synced[-1]["end"] = end_t
        return synced

    # 2. Count mismatch or no existing words: character-weighted interpolation
    total_chars = sum(max(1, len(tok)) for tok in tokens)
    current_time = start_t
    synced = []

    for idx, tok in enumerate(tokens):
        tok_len = max(1, len(tok))
        w_dur = (tok_len / total_chars) * duration
        w_start = round(current_time, 3)
        w_end = round(min(end_t, current_time + w_dur), 3)

        synced.append({
            "word": tok,
            "start": w_start,
            "end": max(round(w_start + 0.03, 3), w_end),
            "probability": 1.0
        })
        current_time += w_dur

    if synced:
        synced[-1]["end"] = end_t

    return synced

def seconds_to_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp: 00:00:00,000"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def seconds_to_vtt_time(seconds: float) -> str:
    """Format seconds into WebVTT timestamp: 00:00:00.000"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def seconds_to_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp: H:MM:SS.cc (centiseconds)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def color_hex_to_ass(hex_color: str, alpha: float = 1.0) -> str:
    """
    Convert #RRGGBB or #RGB to ASS &HAABBGGRR format.
    ASS colors are in BGR order with alpha 00 = opaque, FF = transparent.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        hex_color = "FFFFFF"
    
    r = hex_color[0:2]
    g = hex_color[2:4]
    b = hex_color[4:6]
    
    # ASS alpha is inverted: 00 is fully opaque, FF is fully transparent
    ass_alpha = int(round((1.0 - max(0.0, min(1.0, alpha))) * 255))
    return f"&H{ass_alpha:02X}{b}{g}{r}"

def generate_standard_srt(segments: List[Dict[str, Any]]) -> str:
    """
    Builds strict standard SRT subtitle string.
    """
    lines = []
    for idx, seg in enumerate(segments, start=1):
        start = seconds_to_srt_time(float(seg["start"]))
        end = seconds_to_srt_time(float(seg["end"]))
        text = seg["text"].strip()
        lines.append(f"{idx}\r\n{start} --> {end}\r\n{text}\r\n")
    return "\r\n".join(lines)

def generate_word_level_srt(segments: List[Dict[str, Any]]) -> str:
    """
    Builds word-level SRT where every word has its own sequence and duration.
    Ideal for CapCut word-by-word animation effects.
    Always guarantees synchronization with segment text.
    """
    lines = []
    counter = 1
    for seg in segments:
        text = seg.get("text", "").strip()
        words = seg.get("words", [])
        
        # Ensure words are always synchronized with the edited text
        synced_words = sync_words_with_text(text, words, float(seg["start"]), float(seg["end"]))
        if synced_words:
            for w in synced_words:
                word_text = w.get("word", "").strip()
                if not word_text:
                    continue
                start = seconds_to_srt_time(float(w["start"]))
                end = seconds_to_srt_time(float(w["end"]))
                lines.append(f"{counter}\r\n{start} --> {end}\r\n{word_text}\r\n")
                counter += 1
        elif text:
            # Fallback if no words could be generated
            start = seconds_to_srt_time(float(seg["start"]))
            end = seconds_to_srt_time(float(seg["end"]))
            lines.append(f"{counter}\r\n{start} --> {end}\r\n{text}\r\n")
            counter += 1
    return "\r\n".join(lines)

def generate_vtt(segments: List[Dict[str, Any]]) -> str:
    """
    Builds WebVTT subtitle file content.
    """
    lines = ["WEBVTT\n"]
    for idx, seg in enumerate(segments, start=1):
        start = seconds_to_vtt_time(float(seg["start"]))
        end = seconds_to_vtt_time(float(seg["end"]))
        text = seg["text"].strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def generate_plain_text(segments: List[Dict[str, Any]]) -> str:
    """
    Builds continuous plain transcript text.
    """
    return "\n".join(seg["text"].strip() for seg in segments if seg["text"].strip())

def generate_ass(
    segments: List[Dict[str, Any]],
    style: Optional[Dict[str, Any]] = None,
    video_width: int = 1080,
    video_height: int = 1920
) -> str:
    """
    Builds an Advanced SubStation Alpha (.ass) script with styling.
    """
    s = style or {}
    font_name = s.get("fontFamily", "Montserrat, Arial, sans-serif").split(",")[0].strip()
    font_size = int(s.get("fontSize", 42))
    primary_color = color_hex_to_ass(s.get("textColor", "#FFFFFF"))
    outline_color = color_hex_to_ass(s.get("outlineColor", "#000000"))
    back_color = color_hex_to_ass(s.get("shadowColor", "#000000"), alpha=0.8)
    outline_width = int(s.get("outlineWidth", 3))
    shadow_depth = int(s.get("shadowDepth", 1))
    bold = -1 if s.get("isBold", True) else 0
    italic = -1 if s.get("isItalic", False) else 0
    
    # Alignment: 2 = bottom-center, 8 = top-center, 5 = middle-center
    alignment = int(s.get("alignment", 2))
    margin_v = int(s.get("marginV", 180)) # Distance from bottom or top

    header = f"""[Script Info]
Title: IndoCaption Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},{back_color},{bold},{italic},0,0,100,100,0,0,1,{outline_width},{shadow_depth},{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for seg in segments:
        start_ass = seconds_to_ass_time(float(seg["start"]))
        end_ass = seconds_to_ass_time(float(seg["end"]))
        # Replace newlines with \N for ASS
        text = seg["text"].replace("\r\n", "\\N").replace("\n", "\\N").replace("\r", "\\N")
        events.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")

    return header + "\n".join(events) + "\n"

def resegment_by_words_or_chars(
    segments: List[Dict[str, Any]],
    max_words: int = 4,
    max_chars: int = 28
) -> List[Dict[str, Any]]:
    """
    Splits or regroups segments into shorter, punchy lines suitable for TikTok/Reels/Shorts
    (strictly max 4-5 words or ~28 characters per line) with natural punctuation splitting.
    """
    new_segments = []
    seq = 1

    for seg in segments:
        words = seg.get("words", [])
        if not words:
            # Fallback: split text by space
            text_tokens = seg["text"].split()
            if len(text_tokens) <= max_words:
                new_segments.append({**seg, "sequence": seq})
                seq += 1
            else:
                total_duration = max(0.1, float(seg["end"]) - float(seg["start"]))
                chunk_size = max_words
                for i in range(0, len(text_tokens), chunk_size):
                    chunk = text_tokens[i : i + chunk_size]
                    sub_start = float(seg["start"]) + (i / len(text_tokens)) * total_duration
                    sub_end = float(seg["start"]) + (min(len(text_tokens), i + chunk_size) / len(text_tokens)) * total_duration
                    new_segments.append({
                        "sequence": seq,
                        "start": round(sub_start, 3),
                        "end": round(sub_end, 3),
                        "text": " ".join(chunk),
                        "words": []
                    })
                    seq += 1
            continue

        # Process with precise word-level timestamps
        current_chunk_words = []
        current_char_count = 0

        for idx_w, w in enumerate(words):
            word_str = w.get("word", "").strip()
            if not word_str:
                continue

            would_exceed_words = len(current_chunk_words) >= max_words
            would_exceed_chars = (current_char_count + len(word_str) + 1) > max_chars and len(current_chunk_words) > 0
            
            # Check pause gap with previous word (>0.35s is a natural pause/breath)
            pause_detected = False
            if current_chunk_words and len(current_chunk_words) >= 2:
                gap = float(w.get("start", 0)) - float(current_chunk_words[-1].get("end", 0))
                if gap >= 0.35:
                    pause_detected = True

            # Check punctuation on previous word (comma, dot, question, exclamation)
            punctuation_split = False
            if current_chunk_words and len(current_chunk_words) >= 3:
                last_word = current_chunk_words[-1].get("word", "")
                if last_word.endswith((",", ".", "!", "?", ";", ":")):
                    punctuation_split = True

            if would_exceed_words or would_exceed_chars or pause_detected or punctuation_split:
                # Flush current chunk
                start_t = current_chunk_words[0]["start"]
                end_t = current_chunk_words[-1]["end"]
                text_t = " ".join(cw["word"] for cw in current_chunk_words)
                new_segments.append({
                    "sequence": seq,
                    "start": round(start_t, 3),
                    "end": round(end_t, 3),
                    "text": text_t,
                    "words": list(current_chunk_words)
                })
                seq += 1
                current_chunk_words = [w]
                current_char_count = len(word_str)
            else:
                current_chunk_words.append(w)
                current_char_count += len(word_str) + 1

        # Flush remaining words in segment
        if current_chunk_words:
            start_t = current_chunk_words[0]["start"]
            end_t = current_chunk_words[-1]["end"]
            text_t = " ".join(cw["word"] for cw in current_chunk_words)
            new_segments.append({
                "sequence": seq,
                "start": round(start_t, 3),
                "end": round(end_t, 3),
                "text": text_t,
                "words": list(current_chunk_words)
            })
            seq += 1

    return new_segments

