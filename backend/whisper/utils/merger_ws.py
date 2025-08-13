from whisper.models.whisper_response import WordSegment

# --- helper: build utterances from WordSegment stream (speaker-aware) ---
def words_to_utterances_from_ws(
    words: list[WordSegment],
    *,
    max_gap_s: float = 0.6,  # new utterance if pause > gap or speaker changes
) -> dict:
    merged = []
    cur_spk = None
    cur = []
    last_end = None

    def flush():
        if not cur:
            return
        start = float(cur[0].start)
        end = float(cur[-1].end)
        spk = cur[0].speaker or "Speaker"
        text = "".join(w.text for w in cur).strip()  # Thai join (no spaces)
        merged.append({
            "start": start,
            "end": end,
            "speaker": spk,
            "text": text,
            "words": [w.model_dump() for w in cur],  # keep per-word detail
        })
        cur.clear()

    for w in words:
        spk = w.speaker or "Speaker"
        s = float(w.start); e = float(w.end)
        if not cur:
            cur_spk, cur, last_end = spk, [w], e
            continue
        if spk != cur_spk or (last_end is not None and s - last_end > max_gap_s):
            flush()
            cur_spk, cur = spk, [w]
        else:
            cur.append(w)
        last_end = e

    flush()
    return {"schema_version": "v1", "segments": merged}