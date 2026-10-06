# DataNotes (React + shadcn/ui)

The notes app for the **Datacenters** subject. In production it is compiled and
served by the Flask container (`../backend`); the API is on the same origin, so
there is no CORS.

## Run in development

Start the API (from `../backend`, using Docker or a local venv), then:

```bash
cd notes-app
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to `http://localhost:5001`.

Set a different API origin with `VITE_API_URL` if you serve the front on a
different host:

```bash
VITE_API_URL=http://10.0.0.12 npm run dev
```
