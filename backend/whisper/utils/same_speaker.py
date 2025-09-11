from typing import List, Dict, Any, Optional

def _join_with_space(left: str, right: str, separator: str = " ") -> str:
    if not right:
        return left or ""
    if not left:
        return right
    return left.rstrip() + separator + right.lstrip()

def merge_turns_by_speaker(
    utterances: List[Dict[str, Any]],
    *,
    max_gap_s: Optional[float] = 0.6,   # None => merge all consecutive same-speaker turns
    joiner: str = " "
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
    prev: Optional[Dict[str, Any]] = None

    for u in utterances:
        if not u.get("text"):
            continue

        speaker = (u.get("speaker") or "Speaker").strip()
        start, end = float(u["start"]), float(u["end"])
        text = str(u.get("text") or "")

        if prev is None:
            prev = {"start": start, "end": end, "speaker": speaker, "text": text}
            if "words" in u:
                prev["words"] = list(u.get("words") or [])
            continue

        same_speaker = (speaker == prev["speaker"])
        gap = start - float(prev["end"])
        small_gap = True if max_gap_s is None else (gap <= max_gap_s)

        if same_speaker and small_gap:
            # Merge into prev
            prev["end"] = max(prev["end"], end)
            if text:
                prev["text"] = _join_with_space(prev["text"], text, joiner)
            if "words" in u:
                prev.setdefault("words", []).extend(u.get("words") or [])
        else:
            # Flush prev
            prev["text"] = prev["text"].strip()
            merged.append(prev)

            # Start new
            prev = {"start": start, "end": end, "speaker": speaker, "text": text}
            if "words" in u:
                prev["words"] = list(u.get("words") or [])

    if prev:
        prev["text"] = prev["text"].strip()
        merged.append(prev)

    return merged
