import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from flask import Flask, abort, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.environ.get("STATIC_DIR", os.path.join(BASE_DIR, "static"))
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://datanotes:datanotes@localhost:5432/datanotes",
)

app = Flask(__name__)


@contextmanager
def db_cursor():
    """Open a connection, commit on success, rollback on error, always close."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def as_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


@app.get("/api/health")
def health():
    try:
        with db_cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except psycopg.Error as err:
        return jsonify({"status": "error", "database": str(err)}), 503
    return jsonify({"status": "ok", "database": "postgresql"})


@app.get("/api/notes")
def list_notes():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM notes ORDER BY updated_at DESC")
        rows = cur.fetchall()
    return jsonify([as_dict(r) for r in rows])


@app.post("/api/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    content = data.get("content") or ""
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO notes (title, content) VALUES (%s, %s) RETURNING *",
            (title, content),
        )
        row = cur.fetchone()
    return jsonify(as_dict(row)), 201


@app.get("/api/notes/<int:note_id>")
def get_note(note_id):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
        row = cur.fetchone()
    if row is None:
        return jsonify({"error": "note not found"}), 404
    return jsonify(as_dict(row))


@app.put("/api/notes/<int:note_id>")
def update_note(note_id):
    data = request.get_json(silent=True) or {}
    with db_cursor() as cur:
        cur.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
        row = cur.fetchone()
        if row is None:
            return jsonify({"error": "note not found"}), 404
        title = (data.get("title") or row["title"]).strip()
        if not title:
            return jsonify({"error": "title is required"}), 400
        content = data.get("content", row["content"])
        cur.execute(
            "UPDATE notes SET title = %s, content = %s, updated_at = now() "
            "WHERE id = %s RETURNING *",
            (title, content, note_id),
        )
        row = cur.fetchone()
    return jsonify(as_dict(row))


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    with db_cursor() as cur:
        cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        deleted = cur.rowcount
    if deleted == 0:
        return jsonify({"error": "note not found"}), 404
    return "", 204


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:path>")
def frontend(path):
    if path.startswith("api/"):
        abort(404)
    full = os.path.join(STATIC_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
