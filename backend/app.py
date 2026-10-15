import sqlite3

from flask import Flask, g, jsonify, redirect, render_template_string, request, url_for

DB_PATH = "/data/perros.db"

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
    <h1>Lista de nombres de perro</h1>
    <form method="post" action="/add">
      <input type="text" name="name" placeholder="Nombre del perro" required>
      <button type="submit">Añadir</button>
    </form>
    <ul>
      {% for p in perros %}
        <li>
          <form method="post" action="/delete/{{ p[0] }}"><button class="del" type="submit">Quitar</button></form>
          <strong>{{ p[1] }}</strong>
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
            "CREATE TABLE IF NOT EXISTS perros ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL"
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
    cur = db().execute("SELECT * FROM perros ORDER BY id DESC")
    return render_template_string(PAGE, perros=cur.fetchall())


@app.post("/add")
def add():
    name = request.form.get("name", "").strip()
    if name:
        db().execute("INSERT INTO perros (name) VALUES (?)", (name,))
        db().commit()
    return redirect(url_for("index"))


@app.post("/delete/<int:dog_id>")
def delete(dog_id):
    db().execute("DELETE FROM perros WHERE id = ?", (dog_id,))
    db().commit()
    return redirect(url_for("index"))


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "database": "sqlite"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
