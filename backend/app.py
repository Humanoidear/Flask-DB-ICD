import sqlite3

from flask import Flask, g, jsonify, redirect, render_template_string, request, url_for

DB_PATH = "/data/notes.db"

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Intranet corporativa</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
    .wrap { max-width: 640px; margin: 0 auto; }
    .badge { display: inline-block; background: #16a34a; color: #fff; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; padding: 6px 14px; border-radius: 999px; }
    h1 { font-size: 24px; margin: 18px 0; }
    form { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
    input[type=text] { flex: 1; min-width: 140px; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #f1f5f9; }
    button { padding: 10px 16px; border: 0; border-radius: 8px; background: #2563eb; color: #fff; cursor: pointer; }
    ul { list-style: none; padding: 0; }
    li { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px; }
    li small { color: #94a3b8; }
    .del { background: #dc2626; float: right; padding: 6px 12px; }
  </style>
</head>
<body>
  <div class="wrap">
    <span class="badge">Intranet corporativa</span>
    <h1>Aplicación de notas (Flask + SQLite)</h1>
    <form method="post" action="/add">
      <input type="text" name="title" placeholder="Título" required>
      <input type="text" name="content" placeholder="Contenido">
      <button type="submit">Añadir</button>
    </form>
    <ul>
      {% for n in notes %}
        <li>
          <form method="post" action="/delete/{{ n[0] }}"><button class="del" type="submit">Borrar</button></form>
          <strong>{{ n[1] }}</strong><br>
          {{ n[2] }}<br>
          <small>{{ n[3] }}</small>
        </li>
      {% endfor %}
    </ul>
  </div>
</body>
</html>
"""


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " title TEXT NOT NULL,"
            " content TEXT NOT NULL DEFAULT '',"
            " created_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@app.get("/")
def index():
    cur = db().execute("SELECT * FROM notes ORDER BY id DESC")
    return render_template_string(PAGE, notes=cur.fetchall())


@app.post("/add")
def add():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "")
    if title:
        db().execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
        db().commit()
    return redirect(url_for("index"))


@app.post("/delete/<int:note_id>")
def delete(note_id):
    db().execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db().commit()
    return redirect(url_for("index"))


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "database": "sqlite"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
