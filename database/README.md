# DataNotes — database (SGBD)

PostgreSQL 16 in Docker. This is the only service that stores data. The schema
and seed notes are in `init/01_init.sql`, loaded on first start.

## Run

```bash
cd database
cp .env.example .env      # then edit POSTGRES_PASSWORD
docker compose up -d
```

Listens on port **5432**. The app container connects using `DATABASE_URL`.

To wipe and reseed, remove the volume:

```bash
docker compose down -v && docker compose up -d
```
