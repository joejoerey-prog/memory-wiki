import os
import json
from pathlib import Path
from datetime import datetime

# Paths
SESSIONS_DIR = Path.home() / ".hermes" / "sessions"
OBSIDIAN_DIRS = [
    Path.home() / "Documents" / "memory",
    Path.home() / "Documents" / "hermes-memory" / "memory"
]
OUTPUT_DIR = Path.home() / "memory-wiki" / "docs"

def get_sessions():
    sessions = []
    sessions_json = SESSIONS_DIR / "sessions.json"
    if sessions_json.exists():
        with open(sessions_json, "r") as f:
            data = json.load(f)
            for session_key, meta in data.items():
                sessions.append({
                    "id": meta.get("session_id", session_key),
                    "title": meta.get("display_name", "Untitled Session"),
                    "date": meta.get("created_at", "Unknown"),
                    "type": "session"
                })
    return sorted(sessions, key=lambda x: x["date"], reverse=True)

def get_obsidian_notes():
    notes = []
    seen_paths = set()
    for base_dir in OBSIDIAN_DIRS:
        if not base_dir.exists():
            continue
        for md_file in base_dir.rglob("*.md"):
            if md_file.name.startswith("."):
                continue
            # Use absolute path to deduplicate if files exist in both
            abs_path = str(md_file.resolve())
            if abs_path in seen_paths:
                continue
            seen_paths.add(abs_path)

            notes.append({
                "title": md_file.stem.replace("-", " ").title(),
                "path": str(md_file),
                "safe_name": md_file.name.replace(" ", "_"),
                "date": md_file.stat().st_mtime,
                "type": "note"
            })
    return sorted(notes, key=lambda x: x["date"], reverse=True)

def build_detail_pages(sessions, notes):
    for s in sessions:
        session_file = SESSIONS_DIR / f"session_{s['id']}.json"
        content = "<p>No transcript found for this session.</p>"
        if session_file.exists():
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                    msgs = data.get("messages", [])
                    content = "<ul>"
                    for msg in msgs[:50]:
                        role = msg.get("role", "unknown").capitalize()
                        text = msg.get("content", "")
                        if isinstance(text, list):
                            text = " ".join([t.get("text", "") for t in text if t.get("type") == "text"])
                        text = text.replace("<", "&lt;").replace(">", "&gt;")
                        content += f"<li><strong>{role}:</strong> {text[:500]}{'...' if len(text) > 500 else ''}</li>"
                    content += "</ul>"
            except Exception as e:
                content = f"<p>Error reading session: {e}</p>"

        html = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{s["title"]} - Memory Wiki</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .back {{ display: inline-block; margin-bottom: 20px; color: #0066cc; text-decoration: none; }}
        .back:hover {{ text-decoration: underline; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ padding: 10px; border-bottom: 1px solid #eee; }}
        strong {{ color: #333; }}
    </style>
</head>
<body>
    <a href="index.html" class="back">&larr; Back to Index</a>
    <h1>{s["title"]}</h1>
    <p><em>Date: {s["date"]}</em></p>
    {content}
</body>
</html>"""
        with open(OUTPUT_DIR / f"session_{s['id']}.html", "w") as f:
            f.write(html)

    for n in notes:
        try:
            with open(n["path"], "r") as f:
                md_content = f.read()
            html_content = md_content.replace("\n", "<br>\n").replace("**", "<strong>").replace("*", "<em>")
        except Exception as e:
            html_content = f"<p>Error reading note: {e}</p>"

        html = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{n["title"]} - Memory Wiki</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .back {{ display: inline-block; margin-bottom: 20px; color: #0066cc; text-decoration: none; }}
        .back:hover {{ text-decoration: underline; }}
        .note-content {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <a href="index.html" class="back">&larr; Back to Index</a>
    <h1>{n["title"]}</h1>
    <div class="note-content">{html_content}</div>
</body>
</html>"""
        with open(OUTPUT_DIR / f"note_{n['safe_name']}.html", "w") as f:
            f.write(html)

def build():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sessions = get_sessions()
    notes = get_obsidian_notes()

    build_detail_pages(sessions, notes)

    html = """<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Wiki</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .section { margin-bottom: 40px; }
        .item { padding: 10px; border-bottom: 1px solid #eee; }
        .item a { text-decoration: none; color: #0066cc; font-weight: bold; }
        .item a:hover { text-decoration: underline; }
        .date { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Memory Wiki</h1>

    <div class="section">
        <h2>Daily Logs (Sessions)</h2>
"""
    for s in sessions:
        html += f'        <div class="item"><a href="session_{s["id"]}.html">{s["title"]}</a><br><span class="date">{s["date"]}</span></div>\n'

    html += """    </div>

    <div class="section">
        <h2>Subjects (Obsidian Notes)</h2>
"""
    for n in notes:
        html += f'        <div class="item"><a href="note_{n["safe_name"]}.html">{n["title"]}</a><br><span class="date">Modified: {datetime.fromtimestamp(n["date"]).strftime("%Y-%m-%d")}</span></div>\n'

    html += """    </div>
</body>
</html>
"""

    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(html)

    print(f"Build complete. Generated index.html, {len(sessions)} session pages, and {len(notes)} note pages.")

if __name__ == "__main__":
    build()
