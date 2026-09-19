import json, os, sys, urllib.request
URL=os.environ.get("CATALOG_API","https://TU-SITIO/api/sync")
TOKEN=os.environ.get("SYNC_TOKEN","cambia-esta-clave")
FILE=sys.argv[1] if len(sys.argv)>1 else "ventas_pendientes.jsonl"
if not os.path.exists(FILE): print("No hay ventas pendientes."); raise SystemExit
events=[json.loads(x) for x in open(FILE,encoding="utf-8") if x.strip()]
req=urllib.request.Request(URL,data=json.dumps(events).encode(),headers={"Content-Type":"application/json","X-Sync-Token":TOKEN},method="POST")
print(urllib.request.urlopen(req,timeout=30).read().decode())
