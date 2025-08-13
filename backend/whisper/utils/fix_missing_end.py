def _fix_missing_ends(chunks, default_dur=0.24):
    for i, c in enumerate(chunks):
        c0, c1 = c.get("timestamp", (None, None))
        if c0 is None:
            continue
        if c1 is None:
            next_c0 = None
            if i + 1 < len(chunks):
                next_c0 = chunks[i+1].get("timestamp", (None, None))[0]
            if next_c0 is not None and next_c0 > c0:
                c1 = next_c0
            else:
                c1 = c0 + default_dur
            c["timestamp"] = (c0, c1)
    return chunks
