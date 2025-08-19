def _format_final_text(final_json: dict) -> str:
    es = final_json.get("executive_summary", "").strip()
    decisions = final_json.get("decisions", []) or []
    actions = final_json.get("action_items", []) or []

    lines = []
    if es:
        lines.append("# Executive Summary" + es.strip() + "")
        
    if decisions:
        lines.append("# Decisions")
        for d in decisions:
            lines.append(f"- {d}")
        lines.append("")
    if actions:
        lines.append("# Action Items")
        for a in actions:
            owner = a.get("owner") or "Unassigned"
            item = a.get("item") or ""
            due = a.get("due")
            suffix = f" (due: {due})" if due else ""
            lines.append(f"- [{owner}] {item}{suffix}")
        lines.append("")
    return "".join(lines).strip()