# DataNotes — Datacenters project

A note taking app split across three servers, each containerized with Docker
and meant to run in its own Proxmox LXC container.

| CT  | Service                  | Folder       | Stack                        | Port |
| --- | ------------------------ | ------------ | ---------------------------- | ---- |
| 200 | Database (SGBD)          | `database/`  | PostgreSQL 16                | 5432 |
| 201 | App (API + notes UI)     | `backend/`, `notes-app/` | Flask + gunicorn + React + shadcn/ui | 80 |
| 202 | Public landing page      | `landing/`   | nginx + static HTML/CSS/JS   | 80 |

```
browser ──▶ landing (nginx)      advertises the app, links to it
browser ──▶ app (Flask)          serves the built React SPA + /api, talks to the DB
app     ──▶ database (Postgres)  stores the notes
```

The React frontend is compiled into the Flask image (multi-stage Docker build)
and served from the same origin, so there is no CORS to configure.

## Deploy on Proxmox

On the Proxmox host, with this repository present:

```bash
cd proxmox
sudo ./create-cts.sh     # create the 3 LXCs and install Docker
sudo ./deploy.sh         # copy the code and start the stacks
```

See `proxmox/README.md` for prerequisites, the network settings in
`proxmox/config.env`, and troubleshooting.

## Run locally with Docker

```bash
# 1. database
cd database && cp .env.example .env && docker compose up -d

# 2. app (builds the React frontend, serves it + the API on :80)
cd ../backend && cp .env.example .env   # point DATABASE_URL at the DB
docker compose up -d --build

# 3. landing
cd ../landing && docker compose up -d
```

## Development (no Docker)

```bash
cd database && docker compose up -d                 # PostgreSQL
cd ../backend && python app.py                      # API on :5001
cd ../notes-app && npm run dev                      # UI on :5173 (proxies /api)
cd ../landing && python3 -m http.server 8000        # landing on :8000
```

## Folders

- `database/` — Docker Compose for PostgreSQL, schema + seed in `init/`.
- `backend/` — Flask REST API, `Dockerfile`, Compose. Serves the SPA and `/api`.
- `notes-app/` — React + shadcn/ui + Tailwind source for the notes app.
- `landing/` — static Apple-style advertising site (`config.js` sets the app URL).
- `proxmox/` — LXC creation and deployment scripts + docs.
