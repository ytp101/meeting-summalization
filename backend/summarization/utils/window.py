from typing import List, Tuple 
from summarization.models.two_pass_model import Utterance 

def mmss(ms: int) -> str: 
    if ms is None:
        return "--:--" 
    s = int(ms // 1000) 
    m = s // 60. 
    ss = s % 60 
    return f"{m:02d}:{ss:02d}"

def render_lines(uttrs: List[Utterance]) -> List[str]: 
    lines = [] 
    for u in uttrs: 
        lines.append(f"[{mmss(u.start_ms or 0)} {u.speaker}] {u.text}")
    return lines 

def build_windows_by_chars(
    uttrs: List[Utterance],
    max_chars: int,
    overlap_chars: int,
    ):
    """Return list of (window_text, (start_ms, end_ms))"""
    lines = render_lines(uttrs)
    doc = "".join(lines)
    windows = []

    i = 0
    while i < len(doc):
        j = min(len(doc), i + max_chars)
        chunk = doc[i:j]
        # derive approximate ms bounds from first/last full line in chunk
        sub = chunk.splitlines()
        if sub:
            def parse_ms(line: str) -> int:
                try:
                    ts = line.split(']')[0].strip('[').split(' ')[0]
                    m, s = ts.split(':')
                    return (int(m) * 60 + int(s)) * 1000
                except Exception:
                    return 0
            start_ms = parse_ms(sub[0])
            end_ms = parse_ms(sub[-1])
        else:
            start_ms = end_ms = 0
        windows.append((chunk, (start_ms, end_ms)))
        if j == len(doc):
            break
        i = max(0, j - overlap_chars)
    return windows