# Daily Message

A modular Python project that compiles a personalized daily summary — weather, a to-do list, upcoming school assignments, and your Valorant store — and sends it to your phone via SMS.

Built as a personal project; modules are designed to be importable and used independently.

## Status

| Module | Status | Notes |
|---|---|---|
| `weather.py` | ✅ Working | Tested |
| `todolist.py` | ✅ Working | Tested |
| `canvas.py` | ⚠️ Deprecated | Code is present but no longer maintained |
| `valorantshop.py` | ⚠️ Deprecated | Riot auth library is archived and unreliable; original image-generation feature has been removed |
| SMS sender | Not included | Bring/make your own — see [SMS sending](#sms-sending) below |

## Installation

Clone the repo and install dependencies:

```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

or

```bash
pip install requests python-dotenv
```

## Configuration

Create a file literally named `.env` in the project root (no filename, just the extension). Copy from `.env.example` and fill in your values:

```env
# --- Weather (required for weather.py) ---
# Get coordinates from Google Maps: right-click your location, the lat/lon
# appears at the top of the menu. Click them once to copy.
WEATHER_LAT=40.7128
WEATHER_LON=-74.0060
WEATHER_CITY=New York, NY

# Canvas
CANVAS_URL=https://your-school.instructure.com
CANVAS_TOKEN=your_canvas_api_token
CANVAS_DAYS_AHEAD=7

# --- To-do list (optional) ---
TODO_FILE=todos.json
```

**Important:** add `.env` to your `.gitignore` so you don't accidentally commit your secrets.

## Usage

### Weather

Returns a formatted multi-line string with today's high/low, conditions, hourly forecast from 9 AM to 9 PM, and alerts (umbrella warnings, freeze warnings, etc.).

```python
import weather
message = weather.get_weather_message()
print(message)
```

Run directly to test:

```bash
python weather.py
```

Sample output as a text message (the `/help` reply from the todo module is also visible here):

<img width="400" alt="Weather forecast and /help command shown as SMS messages" src="https://github.com/user-attachments/assets/e348b4f3-fb12-4b3a-ad7d-8833c861bca1" />

### To-do list

Stores tasks in a local JSON file. Commands are designed to be triggered from incoming SMS messages.

**As a library:**

```python
import todolist

todolist.add_task("buy milk")
todolist.remove_task(1)
todolist.clear_tasks()

print(todolist.format_list_message())
```

**From SMS:** pass the message body to `process_command()`:

```python
reply = todolist.process_command(incoming_message_text)
if reply:
    send_sms(sender, reply)
```

**Supported commands** (case-insensitive, leading slash required):

| Command | Action |
|---|---|
| `/add <task>` | Add a task |
| `/remove <n>` | Remove task number `n` |
| `/done` | Clear the entire list |
| `/list` | Show current list |
| `/help` | Show command reference |

Example session over SMS:

<img width="400" alt="To-do list commands demonstrated over SMS" src="https://github.com/user-attachments/assets/dc1823bf-5d21-43b4-8c4c-f845d58658a1" />

Test interactively:

```bash
python todolist.py
```

### Canvas (deprecated)

> ⚠️ This module is no longer maintained and may break with future Canvas API changes.

If you still want to try it:

1. Get a Canvas API token: log into Canvas → profile picture → Account → Settings → "+ New Access Token"
2. Add `CANVAS_URL` and `CANVAS_TOKEN` to your `.env`

### Valorant store (deprecated)

> ⚠️ This module is no longer maintained. The `python-riot-auth` library it depends on was archived in September 2024, and Riot's auth flow has become increasingly unreliable for automation. Expect breakage.

Accounts with MFA enabled will prompt for a code each run, making this unsuitable for automated/scheduled use. The previous image-generation feature (combining skin icons into a daily-store graphic) has been removed.

## SMS sending

This project does **not** include the SMS sender. Make/get your own:

- **[Twilio](https://www.twilio.com/)** — paid, reliable, well-documented. Recommended for anything important.
- **[TextBelt](https://textbelt.com/)** — one free text per day, no signup needed.
- **Email-to-SMS gateways** — most US carriers let you email `phonenumber@carrier-gateway.com` (e.g. `5551234567@vtext.com` for Verizon). Free, no API needed, but unreliable and may be filtered as spam.

Whichever you pick, the integration point is the same: each module exposes a function returning a string, and you concatenate those strings into the final message body.

If your sender supports reading incoming messages, you can wire `todolist.process_command()` into it to handle commands from SMS in real time. Example server-side log of incoming commands being handled and replied to:

<img width="700" alt="Server log showing /help, /add, /remove, and /done commands being processed" src="https://github.com/user-attachments/assets/fd7daba9-cdf7-4ff2-b0aa-3a2a93206844" />

## Putting it all together

Example daily-message script:

```python
import weather
import todolist
# import canvas       # if you want to risk the deprecated module
# import valorantshop # if you want to risk the deprecated module

def build_daily_message(name="friend"):
    sections = [
        f"Good morning, {name}!",
        "",
        weather.get_weather_message(),
        "",
        todolist.format_list_message(),
    ]
    return "\n".join(sections)

if __name__ == "__main__":
    print(build_daily_message("Alex"))
    # send_sms(your_number, build_daily_message("Alex"))
```

## Project structure

```
.
├── README.md
├── .env.example      # template
├── .gitignore
├── weather.py        # ✅ working
├── todolist.py       # ✅ working
├── canvas.py         # ⚠️ deprecated
├── valorantshop.py   # ⚠️ deprecated removed
├── todos.json        # auto-generated by todolist
└── requirements.txt
```

## Troubleshooting

**Weather coordinates wrong:** the `.env` lat/lon must be decimal degrees, not degrees-minutes-seconds. Use Google Maps and right-click — copy the numbers it shows directly.

**To-do list not persisting:** check that the script has write permission to the directory it's running from. The `todos.json` file is created on the first `/add` command.
