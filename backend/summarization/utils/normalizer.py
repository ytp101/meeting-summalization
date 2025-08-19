from typing import List 
from summarization.models.two_pass_model import Utterance 

def _collapse_repeats(text: str) -> str:
    # Deduplicate Thai 'ๆ' runs and collapse whitespace
    import re
    text = re.sub(r"ๆ+", "ๆ", text)
    text = " ".join(text.split())
    return text

def normalize_utterances(
    uttrs: List[Utterance],
    gap_merge_sec: float,
    max_chars_merge: int,
    ) -> List[Utterance]:
    if not uttrs:
        return []
    # sort by start
    us = sorted(uttrs, key=lambda u: (u.start_ms or 0))
    merged: List[Utterance] = []


    def gap_sec(prev: Utterance, cur: Utterance) -> float:
        if prev.end_ms is None or cur.start_ms is None:
            return 9999.0
        return max(0.0, (cur.start_ms - prev.end_ms) / 1000.0)


    for u in us:
        u.text = _collapse_repeats(u.text)
        if not merged:
            merged.append(u)
            continue
        prev = merged[-1]
        same_speaker = (prev.speaker == u.speaker)
        gap_ok = gap_sec(prev, u) <= gap_merge_sec
        size_ok = len((prev.text or "")) + 1 + len((u.text or "")) <= max_chars_merge
        if same_speaker and gap_ok and size_ok:
            prev.text = (prev.text.rstrip() + " " + u.text.lstrip()).strip()
            prev.end_ms = u.end_ms if u.end_ms is not None else prev.end_ms
    # keep prev.start_ms, prev.speaker
    else:
        merged.append(u)


    # final cleanup
    for m in merged:
        m.text = _collapse_repeats(m.text)
    return merged