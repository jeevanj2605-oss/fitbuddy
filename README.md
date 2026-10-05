# FitBuddy — AI Fitness Plan Generator

A FastAPI + Jinja2 + SQLite app based on the supplied FitBuddy documentation. It generates a 7-day activity plan, a nutrition/recovery tip, accepts feedback to revise a plan, and provides a simple coach dashboard.

## Requirements
- Python 3.10+
- A Google AI Studio API key for live Gemini generation (optional; the app has sample fallback content)

## Run in VS Code (Windows)
1. Extract the ZIP and open the `fitbuddy` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use `\.venv\Scripts\activate.bat` from Command Prompt.
4. Install packages:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env`, then put your key after `GOOGLE_API_KEY=`. Keep `.env private; do not commit it.
6. Start the server:
   ```powershell
   uvicorn app.main:app --reload
   ```
7. Open `http://127.0.0.1:8000`. API docs: `http://127.0.0.1:8000/docs`.

## Test
- Visit `/health`; expected response: `{"status":"ok"}`.
- Submit the home form and confirm a plan and tip appear.
- Submit feedback to see the revised plan.
- Visit `/view-all-users` to review saved profiles and plans.
- Visit `/api/users` or `/docs` to test the JSON API.

## Project layout
```text
fitbuddy/
├── app/
│   ├── main.py
│   ├── routes.py
│   ├── ai.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── templates/
│   │   ├── index.html
│   │   ├── result.html
│   │   └── all_users.html
│   └── static/style.css
├── .env.example
├── .gitignore
└── requirements.txt
```

## Notes
- The supplied document names Gemini 1.5 Pro and Gemini Flash. Model availability changes; this implementation uses configurable current model IDs (`GEMINI_PRO_MODEL`, `GEMINI_FLASH_MODEL`) and the official `google-genai` SDK.
- The dashboard is intentionally a local development view and has no authentication. Do not expose it publicly without adding authentication and access controls.
- This is a general wellness planner, not a medical or diet prescription. The age field accepts 13+ and prompts emphasize manageable activity, rest, and non-restrictive nutrition.
