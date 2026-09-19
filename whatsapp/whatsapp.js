import makeWASocket,{useMultiFileAuthState,DisconnectReason} from "@whiskeysockets/baileys";
import Database from "better-sqlite3"; import pino from "pino"; import path from "path";
const DB=process.env.CATALOG_DB||path.resolve("../data/catalogo.sqlite3"); const db=new Database(DB);
const active=new Map(); const norm=s=>(s||"").trim().toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu,"");
const menu=`🛒 *MENÚ*\n\n1. Buscar producto\n2. Catálogo disponible\n3. Quejas\n4. Sugerencias\n\nEscribe *buscar CODIGO/NOMBRE* para buscar.\nEscribe *salir* para cerrar el menú.`;
async function main(){const {state,saveCreds}=await useMultiFileAuthState("auth"); const sock=makeWASocket({auth:state,logger:pino({level:"silent"}),printQRInTerminal:true});
sock.ev.on("creds.update",saveCreds); sock.ev.on("messages.upsert",async ({messages,type})=>{if(type!=="notify")return; for(const m of messages){if(!m.message||m.key.fromMe)continue;
 const jid=m.key.remoteJid; if(jid?.endsWith("@g.us")) continue; const text=m.message.conversation||m.message.extendedTextMessage?.text||""; const t=norm(text);
 if(["menu","inicio","início"].includes(t)){active.set(jid,Date.now()); await sock.sendMessage(jid,{text:menu}); continue}
 if(!active.has(jid)) continue; if(t==="salir"){active.delete(jid);await sock.sendMessage(jid,{text:"✅ Menú cerrado."});continue}
 if(t.startsWith("buscar ")){const q=text.slice(7).trim(); const rs=db.prepare("SELECT * FROM products WHERE codigo LIKE ? OR producto LIKE ? LIMIT 10").all(`%${q}%`,`%${q}%`);
  const out=rs.length?rs.map(p=>`📦 *${p.producto||"Producto"}*\nCódigo: ${p.codigo}\nPrecio: $${Number(p.precio_venta||0).toFixed(2)}\nExistencia: ${p.existencia}`).join("\n\n"):"No encontré productos."; await sock.sendMessage(jid,{text:out}); continue}
 // Deliberately no generic auto-response: personal chats remain quiet unless menu session is active.
}}); sock.ev.on("connection.update",u=>{if(u.connection==="close" && u.lastDisconnect?.error?.output?.statusCode!==DisconnectReason.loggedOut)main()});}
main();
