import os, sqlite3
from flask import Flask, jsonify, request, send_from_directory
BASE=os.path.dirname(__file__); DB=os.path.join(BASE,"data","catalogo.sqlite3")
app=Flask(__name__, static_folder="public")
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
@app.get("/")
def home(): return send_from_directory("public","index.html")
@app.get("/catalogo.json")
def catalog_json():
 c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM products ORDER BY producto,codigo")]; c.close(); return jsonify(rows)
@app.get("/api/search")
def search():
 q=(request.args.get("q") or "").strip()
 c=conn(); rows=[dict(x) for x in c.execute("""SELECT * FROM products WHERE codigo LIKE ? OR producto LIKE ? OR departamento LIKE ? ORDER BY producto LIMIT 25""",(f"%{q}%",)*3)]; c.close()
 return jsonify(rows)
@app.post("/api/sync")
def sync():
 token=request.headers.get("X-Sync-Token","")
 if token != os.environ.get("SYNC_TOKEN","cambia-esta-clave"): return jsonify(error="unauthorized"),401
 events=request.get_json(silent=True) or []
 c=conn(); applied=0
 for e in events:
  try:
   cur=c.execute("INSERT OR IGNORE INTO sync_events(event_key,codigo,delta,source) VALUES(?,?,?,?)",(str(e["event_key"]),str(e["codigo"]),float(e["delta"]),str(e.get("source","eleventa"))))
   if cur.rowcount:
    c.execute("UPDATE products SET existencia=MAX(0,existencia+?), actualizado=CURRENT_TIMESTAMP WHERE codigo=?",(float(e["delta"]),str(e["codigo"])))
    c.execute("UPDATE sync_events SET applied_at=CURRENT_TIMESTAMP WHERE event_key=?",(str(e["event_key"]),)); applied+=1
  except Exception: pass
 c.commit(); c.close(); return jsonify(ok=True,applied=applied)
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")))
