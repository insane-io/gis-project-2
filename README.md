# Project-2 — Local setup

FastAPI backend + React (Vite) frontend.

Minimal instructions to run locally.

Prerequisites
- Python 3.10+, pip
- Node.js 16+ and npm

Backend (Linux / macOS)

```bash
cd backend
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend (Windows PowerShell)

```powershell
cd backend
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend

```bash
cd frontend
npm install
npm run dev
```

If the frontend needs to call the backend, set the API URL in `frontend/.env` (Vite reads variables starting with `VITE_`):

```bash
VITE_API_URL=http://127.0.0.1:8000
```

Project layout

```
project-2/
├── backend/    # FastAPI app
└── frontend/   # Vite + React
```

That's it — run backend and frontend in separate terminals.
