def _format_final_text(final_json: dict) -> str:
    es = (final_json.get("executive_summary") or "").strip()
    decisions = final_json.get("decisions") or []
    actions = final_json.get("action_items") or []

    lines: list[str] = []

    # Executive Summary
    if es:
        lines.append("## 📝 Executive Summary")
        lines.append(es)
        lines.append("")  # blank line

    # Decisions
    if decisions:
        lines.append("## ✅ Decisions")
        for d in decisions:
            d_str = (str(d) if not isinstance(d, dict) else d.get("text") or d.get("decision") or "")
            d_str = d_str.strip()
            if d_str:
                lines.append(f"- {d_str}")
        lines.append("")

    # Action Items
    if actions:
        lines.append("## 📌 Action Items")
        for a in actions:
            if isinstance(a, dict):
                owner = (a.get("owner") or "Unassigned").strip()
                item = (a.get("item") or a.get("task") or "").strip()
                if not item:
                    continue
                due = (a.get("due") or "").strip()
                due_str = f" (due: {due})" if due else ""
                lines.append(f"- [ ] **{item}** — *{owner}*{due_str}")
            else:
                # fall back if model returned a plain string
                s = str(a).strip()
                if s:
                    lines.append(f"- [ ] {s}")
        lines.append("")

    # Ensure stable markdown with proper newlines
    return "\n".join(lines).strip() + "\n"
