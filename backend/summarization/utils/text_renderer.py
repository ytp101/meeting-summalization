def format_summary(raw: str) -> str:
    # Ensure required sections
    if "Executive Summary" not in raw:
        raw = "## 📝 Executive Summary\n" + raw
    if "Decisions" not in raw:
        raw += "\n\n## ✅ Decisions\n- None noted"
    if "Action Items" not in raw:
        raw += "\n\n## 📌 Action Items\n- [ ] None assigned"

    return raw.strip()
