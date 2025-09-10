from typing import List, Dict, Any, Optional

def merge_turns_by_speaker(
    utterances: List[Dict[str, Any]],
    *,
    max_gap_s: Optional[float] = 0.6,   # None => ignore gaps (merge all consecutive same-speaker)
    joiner: str = " "                   # default: space for Latin languages
) -> List[Dict[str, Any]]:
    """
    Merge consecutive turns if same speaker and (optionally) the gap is small.
    Keeps first start, last end; concatenates text with `joiner`.
    """
    if not utterances:
        return []

    # Ensure chronological order
    utterances = sorted(utterances, key=lambda u: float(u["start"]))

    merged: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None

    for u in utterances:
        if not u.get("text"):
            continue

        spk = (u.get("speaker") or "Speaker").strip()
        s, e = float(u["start"]), float(u["end"])
        text = (u["text"] or "")

        if cur is None:
            cur = {"start": s, "end": e, "speaker": spk, "text": text}
            if "words" in u:
                cur["words"] = list(u.get("words") or [])
            continue

        same_speaker = (spk == cur["speaker"])
        gap = s - float(cur["end"])
        small_gap = True if max_gap_s is None else (gap <= max_gap_s)

        if same_speaker and small_gap:
            cur["end"] = max(cur["end"], e)
            if text:
                # Always add joiner between consecutive fragments
                cur["text"] = cur["text"] + joiner + text
            if "words" in u:
                cur.setdefault("words", []).extend(u.get("words") or [])
        else:
            # Clean up before storing
            cur["text"] = cur["text"].strip()
            merged.append(cur)
            cur = {"start": s, "end": e, "speaker": spk, "text": text}
            if "words" in u:
                cur["words"] = list(u.get("words") or [])

    if cur:
        cur["text"] = cur["text"].strip()
        merged.append(cur)

    return merged
