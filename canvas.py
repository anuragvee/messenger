
import os
from datetime import datetime, timedelta, timezone
import requests
from dotenv import load_dotenv


load_dotenv()
CANVAS_URL = (os.getenv("CANVAS_URL") or "").rstrip("/")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
DAYS_AHEAD = int(os.getenv("CANVAS_DAYS_AHEAD", "7"))

if not CANVAS_URL or not CANVAS_TOKEN:
    raise RuntimeError(
        "Missing CANVAS_URL or CANVAS_TOKEN in .env. "
        "See module docstring for setup instructions."
    )


HEADERS = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
RELEVANT_TYPES = {"assignment", "quiz", "discussion_topic", "wiki_page"}

TYPE_LABELS = {
    "assignment": "Assignment",
    "quiz": "Quiz",
    "discussion_topic": "Discussion",
    "wiki_page": "Page",
}



def _fetch_planner_items(start_date, end_date):
    """
    Fetch all planner items in the given date range, following pagination.
    Canvas paginates with Link headers; aiohttp/requests exposes them via .links.
    """
    items = []
    url = f"{CANVAS_URL}/api/v1/planner/items"
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "per_page": 50,
    }

    while url:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        items.extend(resp.json())
        next_link = resp.links.get("next", {}).get("url")
        url = next_link
        params = None 
    return items


def _format_due(due_dt, now):
    days_away = (due_dt.date() - now.date()).days
    fmt = "%#I:%M %p" if os.name == "nt" else "%-I:%M %p"
    time_str = due_dt.strftime(fmt)

    if days_away < 0:
        return f"⚠️ OVERDUE ({due_dt.strftime('%a %b %d')})"
    if days_away == 0:
        return f"today at {time_str}"
    if days_away == 1:
        return f"tomorrow at {time_str}"
    if days_away < 7:
        return f"{due_dt.strftime('%A')} at {time_str}"
    return due_dt.strftime("%a %b %d")


def get_assignments():
    now_utc = datetime.now(timezone.utc)
    end_utc = now_utc + timedelta(days=DAYS_AHEAD)

    raw = _fetch_planner_items(now_utc, end_utc)

    assignments = []
    for item in raw:
        if item.get("plannable_type") not in RELEVANT_TYPES:
            continue

        submission = item.get("submissions") or {}
        if isinstance(submission, dict):
            if submission.get("submitted") or submission.get("excused"):
                continue

        plannable = item.get("plannable") or {}
        due_iso = plannable.get("due_at") or item.get("plannable_date")
        if not due_iso:
            continue  

        due_utc = datetime.fromisoformat(due_iso.replace("Z", "+00:00"))
        due_local = due_utc.astimezone()

        html_url = item.get("html_url") or ""
        full_url = f"{CANVAS_URL}{html_url}" if html_url.startswith("/") else html_url

        assignments.append({
            "course": item.get("context_name", "Unknown course"),
            "title": plannable.get("title", "Untitled"),
            "type": item.get("plannable_type"),
            "due_dt": due_local,
            "missing": bool(submission.get("missing")) if isinstance(submission, dict) else False,
            "url": full_url or None,
        })

    assignments.sort(key=lambda a: a["due_dt"])
    return assignments


def get_assignments_message():
    """Return upcoming assignments as a formatted message string."""
    assignments = get_assignments()

    if not assignments:
        return f"📚 No assignments due in the next {DAYS_AHEAD} days. 🎉"

    lines = [f"📚 Upcoming assignments (next {DAYS_AHEAD} days):"]
    now_local = datetime.now().astimezone()

    for a in assignments:
        type_label = TYPE_LABELS.get(a["type"], "Item")
        due_str = _format_due(a["due_dt"], now_local)
        missing_marker = " ⚠️" if a["missing"] else ""
        lines.append(
            f"  • [{type_label}] {a['title']} ({a['course']}){missing_marker}"
        )
        lines.append(f"      due {due_str}")

    return "\n".join(lines)
