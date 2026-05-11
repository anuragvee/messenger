import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

DEFAULT_PATH = Path(__file__).parent / "todos.json"
TODO_FILE = Path(os.getenv("TODO_FILE", DEFAULT_PATH))


HELP_TEXT = (
    "Commands:\n"
    "  /add <task>    Add a task\n"
    "  /remove <n>    Remove task #n\n"
    "  /done          Clear all tasks\n"
    "  /list          Show current list\n"
    "  /help          Show this message"
)

def _load():
    """Read the list from disk. Returns [] if the file is missing or corrupt."""
    if not TODO_FILE.exists():
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save(tasks):
    """Persist the list to disk."""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

def get_tasks():
    """Return the current list of task strings."""
    return _load()

def add_task(task):
    """Add a task to the end of the list. Returns the updated list."""
    task = task.strip()
    if not task:
        raise ValueError("Task can't be empty.")
    tasks = _load()
    tasks.append(task)
    _save(tasks)
    return tasks

def remove_task(number):
    """
    Remove the task at 1-based position `number`.
    Returns the removed task string. Raises IndexError if out of range.
    """
    tasks = _load()
    if number < 1 or number > len(tasks):
        raise IndexError(f"No task #{number} (you have {len(tasks)} tasks).")
    removed = tasks.pop(number - 1)
    _save(tasks)
    return removed

def clear_tasks():
    """Wipe all tasks. Returns the count of tasks that were cleared."""
    tasks = _load()
    count = len(tasks)
    _save([])
    return count

def format_list_message():
    """
    Return the current list as a friendly multi-line string, suitable
    for dropping into a text message or daily summary.
    """
    tasks = _load()
    if not tasks:
        return "📝 To-do list: (empty)"
    lines = ["📝 To-do list:"]
    for i, task in enumerate(tasks, 1):
        lines.append(f"  {i}. {task}")
    return "\n".join(lines)

def process_command(text):
    """
    Parse an incoming message and dispatch to the right action.
    Returns a reply string to send back, or None if the message
    isn't a recognized command (so you can ignore non-commands).

    Recognized commands:
        /add <task>
        /remove <n>
        /done
        /list
        /help

    Anything else starting with '/' falls through to the help message.
    """
    if not text:
        return None

    stripped = text.strip()
    if not stripped.startswith("/"):
        return None  

    parts = stripped.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command == "/add":
        if not args.strip():
            return "Usage: /add <task>"
        try:
            tasks = add_task(args)
        except ValueError as e:
            return f"❌ {e}"
        return f"✅ Added: {args.strip()}\n\n{format_list_message()}"

    if command == "/remove":
        if not args.strip():
            return "Usage: /remove <task number>"
        try:
            number = int(args.strip())
        except ValueError:
            return f"❌ '{args.strip()}' isn't a number. Try: /remove 2"
        try:
            removed = remove_task(number)
        except IndexError as e:
            return f"❌ {e}"
        return f"🗑️ Removed: {removed}\n\n{format_list_message()}"

    if command == "/done":
        count = clear_tasks()
        if count == 0:
            return "Your list was already empty. 🎉"
        return f"🎉 Cleared {count} task{'s' if count != 1 else ''}!\n\n{format_list_message()}"

    if command == "/list":
        return format_list_message()

    if command == "/help":
        return HELP_TEXT

    return HELP_TEXT
