# DataNotes — landing page

A static, Apple-style site advertising the DataNotes app, all in English.
Served by nginx in Docker.

Set the public app URL in `config.js` (`window.DATANOTES_APP_URL`), then:

```bash
cd landing
docker compose up -d
```

Open http://localhost (port **80**).

To preview without Docker:

```bash
python3 -m http.server 8000
```
