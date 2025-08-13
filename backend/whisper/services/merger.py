# utils local to this module (or put in app/utils/merge.py)
from typing import Dict, Any, List, Optional

def words_to_utterances(
    words: List[Dict[str, Any]],
    *,
    joiner: str = "",       # Thai: no space; use " " for Latin if needed
    max_gap_s: float = 0.6  # start new utterance if pause > this gap or speaker changes
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    cur_spk: Optional[str] = None
    cur_words: List[Dict[str, Any]] = []
    last_end: Optional[float] = None

    for w in words:
        spk = w.get("speaker") or "Speaker"
        s, e = float(w["start"]), float(w["end"])

        if not cur_words:
            cur_spk, cur_words, last_end = spk, [w], e
            continue

        # new chunk if speaker changes or a large temporal gap appears
        if spk != cur_spk or (last_end is not None and s - last_end > max_gap_s):
            merged.append(_flush(cur_words, cur_spk, joiner))
            cur_spk, cur_words = spk, [w]
        else:
            cur_words.append(w)

        last_end = e

    if cur_words:
        merged.append(_flush(cur_words, cur_spk, joiner))
    return merged

def _flush(ws: List[Dict[str, Any]], speaker: str, joiner: str) -> Dict[str, Any]:
    start = float(ws[0]["start"]); end = float(ws[-1]["end"])
    # join Thai tokens without spaces; adjust if you prefer smarter Thai tokenization later
    text = joiner.join(w["text"] if "text" in w else w["word"] for w in ws).strip()
    return {"start": start, "end": end, "speaker": speaker, "text": text, "words": ws}
