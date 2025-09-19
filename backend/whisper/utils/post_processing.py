import re

REPEAT_TH = re.compile(r'([ก-๙]+)(?:\s*\1){3,}')
NUM_PCT   = re.compile(r'(\d+(?:[.,]\d+)?)\s*เปอร์เซ็น(?:ต์)?', re.I)
DATE_DMY  = re.compile(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})')
REPEAT_WORD_3PLUS = re.compile(r'(\S+)(?: \1){3,}', re.IGNORECASE)
REPEAT_THAI_CHAR_3PLUS = re.compile(r'([\u0E00-\u0E7F])\1{3,}')

def dedup_text(t: str) -> str:
    if not t:
        return ""
    s = REPEAT_THAI_CHAR_3PLUS.sub(lambda m: m.group(1) * 3, t)
    s = REPEAT_WORD_3PLUS.sub(lambda m: " ".join([m.group(1)] * 3), s)
    return s

def normalize_numbers(t: str, *, day_first: bool = True) -> str:
    if not t: return t
    t = NUM_PCT.sub(r"\1%", t)
    def _iso(m):
        a,b,y = m.group(1), m.group(2), m.group(3)
        d,mth = (int(a), int(b)) if day_first else (int(b), int(a))
        y = int(y) + 2000 if int(y) < 100 else int(y)
        return f"{y:04d}-{mth:02d}-{d:02d}"
    return DATE_DMY.sub(_iso, t)

def postprocess_text(t: str, *, day_first: bool = True) -> str:
    return normalize_numbers(dedup_text(t), day_first=day_first)