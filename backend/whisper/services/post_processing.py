import re
from typing import List, Dict, Any

# --- 1) Duplicate removal (>3 repeats) ---
# Thai-friendly: caps runs of the same Thai token (with or without spaces) at 3.
REPEAT_TH = re.compile(r'([ก-๙]+)(?:\s*\1){3,}')

def dedup_text(text: str, joiner: str = " ") -> str:
    """
    Collapse runs of the same Thai token repeated >3 times.
    Example: 'ครับ ครับ ครับ ครับ' -> 'ครับ ครับ ครับ'
    """
    def _cap(m: re.Match) -> str:
        tok = m.group(1)
        return joiner.join([tok, tok, tok])
    return REPEAT_TH.sub(_cap, text or "").strip()

# --- 2) Percent & date normalization ---
# 2a) Percent: "... 50 เปอร์เซ็น/เปอร์เซ็นต์" -> "50%"
NUM_PCT = re.compile(r'(\d+(?:[.,]\d+)?)\s*เปอร์เซ็น(?:ต์)?', flags=re.IGNORECASE)

# 2b) Dates: d/m/yy(yy) or d-m-yy(yy) -> ISO (YYYY-MM-DD)
DATE_DMY = re.compile(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})')

def normalize_numbers(text: str, *, day_first: bool = True) -> str:
    """
    - '50 เปอร์เซ็น(ต์)' -> '50%'
    - '1/8/25' or '01-08-2025' -> '2025-08-01' (assuming day_first=True)
    """
    if not text:
        return text

    # Percent
    text = NUM_PCT.sub(r'\1%', text)

    # Dates
    def _to_iso(m: re.Match) -> str:
        a, b, y = m.group(1), m.group(2), m.group(3)
        d, mth = (int(a), int(b)) if day_first else (int(b), int(a))
        y = int(y)
        if y < 100:  # 2-digit -> 20xx
            y += 2000
        return f"{y:04d}-{mth:02d}-{d:02d}"

    text = DATE_DMY.sub(_to_iso, text)
    return text

# --- 3) One-call wrapper for a single text field ---
def postprocess_text(text: str, *, day_first: bool = True) -> str:
    return normalize_numbers(dedup_text(text), day_first=day_first)

# --- 4) Apply to ASR segments in-place ---
def postprocess_segments(segments: List[Dict[str, Any]], *, day_first: bool = True) -> List[Dict[str, Any]]:
    """
    Mutates each segment's 'text' using the post-processing pipeline.
    Safe for both raw Whisper segments and merged (speaker) segments.
    """
    for s in segments:
        t = s.get("text", "")
        s["text"] = postprocess_text(t, day_first=day_first)
    return segments
