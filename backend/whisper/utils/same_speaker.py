from typing import List, Dict, Any

def merge_turns_by_speaker(
    utterances: List[Dict[str, Any]],
    *,
    max_gap_s: float = 0.6,   # new turn if pause > this
    joiner: str = ""          # "" for Thai, " " for Latin
) -> List[Dict[str, Any]]:
    """
    Input (chronological):
      [{"start": float, "end": float, "speaker": str|None, "text": str, "words": [...]?}, ...]

    Output (chronological, merged when same speaker & small gap):
      [{"start": float, "end": float, "speaker": str, "text": str, "words": [...]?}, ...]
    """
    merged: List[Dict[str, Any]] = []
    cur = None

    for u in utterances:
        if not u.get("text"):
            continue
        spk = u.get("speaker") or "Speaker"
        s, e = float(u["start"]), float(u["end"])
        text = u["text"].strip()

        if cur is None:
            cur = {"start": s, "end": e, "speaker": spk, "text": text}
            if "words" in u: cur["words"] = list(u.get("words") or [])
            continue

        same_speaker = (spk == cur["speaker"])
        small_gap = (s - cur["end"]) <= max_gap_s

        if same_speaker and small_gap:
            cur["end"] = max(cur["end"], e)
            cur["text"] = (cur["text"] + joiner + text).strip()
            if "words" in u:
                cur.setdefault("words", []).extend(u.get("words") or [])
        else:
            merged.append(cur)
            cur = {"start": s, "end": e, "speaker": spk, "text": text}
            if "words" in u: cur["words"] = list(u.get("words") or [])

    if cur: merged.append(cur)
    return merged
