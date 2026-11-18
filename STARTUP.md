# SEO AI Agent – Startup Scripts

## 0. Install dependencies (once)
```powershell
# From project root: e:\SEO Ai Agent
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```
> Important: the API must run with the **same** Python that has these packages
> installed. Running `uvicorn` from a different interpreter (e.g. a global one)
> makes the Off-Page Opportunity Finder fail with `No module named 'ddgs'`.

## Start the Backend API (FastAPI)
```powershell
# From project root: e:\SEO Ai Agent
.\venv\Scripts\python.exe -m uvicorn api:app --reload --port 8000
```

## Start the Frontend (React/Vite)
```powershell
# From: e:\SEO Ai Agent\frontend
npm run dev
```

## Open in Browser
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
