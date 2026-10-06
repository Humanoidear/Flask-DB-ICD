# DataNotes API + frontend (Flask)

Flask serves the JSON API **and** the compiled React app on the same origin.
Data lives in PostgreSQL (see `../database`). Runs in Docker on port **80**
(container port 8000, via gunicorn).

## Run

```bash
cd backend
cp .env.example .env      # point DATABASE_URL at your database server
docker compose up -d --build
```

Open http://localhost. The multi-stage `Dockerfile` builds `../notes-app` with
Node and copies the output into the image as `static/`.

## Endpoints

| Method | Path              | Description    |
| ------ | ----------------- | -------------- |
| GET    | `/api/health`     | Health + DB    |
| GET    | `/api/notes`      | List all notes |
| POST   | `/api/notes`      | Create a note  |
| GET    | `/api/notes/<id>` | Get one note   |
| PUT    | `/api/notes/<id>` | Update a note  |
| DELETE | `/api/notes/<id>` | Delete a note  |

Any other path serves the React single-page app.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://datanotes:change_me_now@localhost:5432/datanotes
python app.py                 # API on :5001, no static files
```

Run `../notes-app` with `npm run dev` for the UI (Vite proxies `/api` to :5001).
