import os
import sqlite3
try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None
from flask import send_from_directory, Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(__file__)
SQLITE_DB = os.path.join(BASE, "data", "catalogo.sqlite3")
DATABASE_URL = os.environ.get("DATABASE_URL")

app = Flask(__name__, static_folder="public")


def pg():
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    con = sqlite3.connect(SQLITE_DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with pg() as c:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    codigo TEXT PRIMARY KEY,
                    producto TEXT,
                    p_costo DOUBLE PRECISION DEFAULT 0,
                    p_venta DOUBLE PRECISION DEFAULT 0,
                    p_mayoreo DOUBLE PRECISION DEFAULT 0,
                    existencia DOUBLE PRECISION DEFAULT 0,
                    inv_minimo DOUBLE PRECISION DEFAULT 0,
                    inv_maximo DOUBLE PRECISION DEFAULT 0,
                    departamento TEXT,
                    foto_url TEXT,
                    actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS sync_events (
                    event_key TEXT PRIMARY KEY,
                    codigo TEXT,
                    delta DOUBLE PRECISION,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied_at TIMESTAMP
                )
            """)

            cur.execute("SELECT COUNT(*) AS n FROM products")
            empty = cur.fetchone()["n"] == 0

        if os.path.exists(SQLITE_DB):
            s = sqlite3.connect(SQLITE_DB)
            s.row_factory = sqlite3.Row
            rows = s.execute("SELECT * FROM products").fetchall()

            with c.cursor() as cur:
                for r in rows:
                    d = dict(r)

                    cur.execute("""
                        INSERT INTO products
                        (codigo, producto, p_costo, p_venta, p_mayoreo,
                         existencia, inv_minimo, inv_maximo, departamento,
                         foto_url)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (codigo) DO UPDATE SET
                            producto=EXCLUDED.producto,
                            p_venta=EXCLUDED.p_venta,
                            p_mayoreo=EXCLUDED.p_mayoreo,
                            departamento=EXCLUDED.departamento,
                            foto_url=EXCLUDED.foto_url,
                            actualizado=CURRENT_TIMESTAMP
                    """, (
                        str(d.get("codigo", "")),
                        d.get("producto"),
                        d.get("p_costo", 0) or 0,
                        d.get("precio_venta", 0) or 0,
                        d.get("precio_mayoreo", 0) or 0,
                        d.get("existencia", 0) or 0,
                        d.get("inv_minimo", 0) or 0,
                        d.get("inv_maximo", 0) or 0,
                        d.get("departamento"),
                        d.get("image_url")
                    ))

            s.close()


@app.get("/")
def home():
    return send_from_directory("public", "index.html")


@app.get("/images/<path:filename>")
def images(filename):
    return send_from_directory("public/images", filename)

@app.get("/catalogo.json")
def catalogo_json():
    with pg() as c:
        cur = c.cursor()
        cur.execute("SELECT * FROM products ORDER BY producto, codigo")
        rows = cur.fetchall()

        if DATABASE_URL:
            return jsonify(rows)

        data = [dict(row) for row in rows]
    for r in data:
        r["p_venta"] = r.get("precio_venta", 0)
        r["p_mayoreo"] = r.get("precio_mayoreo", 0)
        r["foto_url"] = r.get("image_url", "")
    return jsonify(data)


@app.get("/api/search")
def search():
    q = (request.args.get("q") or "").strip()

    with pg() as c:
        with c.cursor() as cur:
            cur.execute("""
                SELECT * FROM products
                WHERE codigo ILIKE %s
                   OR producto ILIKE %s
                   OR departamento ILIKE %s
                ORDER BY producto
                LIMIT 25
            """, (f"%{q}%", f"%{q}%", f"%{q}%"))

            rows = cur.fetchall()
        if not DATABASE_URL:
            rows = [dict(r) for r in rows]
            for r in rows:
                r["p_venta"] = r.get("precio_venta", 0)
                r["p_mayoreo"] = r.get("precio_mayoreo", 0)
                r["foto_url"] = r.get("image_url", "")
                r["foto_url"] = r.get("image_url", "")
        return jsonify(rows)


@app.post("/api/sync")
def sync():
    token = request.headers.get("X-Sync-Token", "")

    if token != os.environ.get("SYNC_TOKEN", "cambia-esta-clave"):
        return jsonify(error="unauthorized"), 401

    events = request.get_json(silent=True) or []
    applied = 0

    with pg() as c:
        with c.cursor() as cur:
            for e in events:
                cur.execute("""
                    INSERT INTO sync_events(event_key,codigo,delta,source)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (event_key) DO NOTHING
                    RETURNING event_key
                """, (
                    str(e["event_key"]),
                    str(e["codigo"]),
                    float(e["delta"]),
                    e.get("source", "eleventa")
                ))

                inserted = cur.fetchone()

                if inserted:
                    cur.execute("""
                        UPDATE products
                        SET existencia=GREATEST(0, existencia + %s),
                            actualizado=CURRENT_TIMESTAMP
                        WHERE codigo=%s
                    """, (
                        float(e["delta"]),
                        str(e["codigo"])
                    ))

                    cur.execute("""
                        UPDATE sync_events
                        SET applied_at=CURRENT_TIMESTAMP
                        WHERE event_key=%s
                    """, (str(e["event_key"]),))

                    applied += 1

    return jsonify(ok=True, applied=applied)


if DATABASE_URL:
    init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080"))
    )
