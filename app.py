# app.py — Portail Render (mot de passe) -> redirection vers Carrd
from datetime import datetime, timezone
from flask import Flask, request, redirect, Response

app = Flask(__name__)

# 🔧 REMPLACE par ton URL Carrd (ex: "https://tonsite.carrd.co")
CARRD_URL = "https://ton-site.carrd.co"

# 🔑 TOKENS (un par séjour). Langue = ancre (#fr, #en, #it, #es)
# mets des dates larges au début pour tester.
TOKENS = [
    {"token": "TESTFR", "lang": "fr", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
    {"token": "TESTEN", "lang": "en", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

HTML = """<!doctype html>
<html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accès guide</title>
<style>
body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;background:#f6f6f9;margin:0}
.wrap{max-width:480px;margin:12vh auto;background:#fff;padding:24px;border-radius:16px;
      box-shadow:0 10px 30px rgba(0,0,0,.08)}
h1{font-size:20px;margin:0 0 10px} p{margin:0 0 14px;color:#444}
input,button{padding:12px 14px;border-radius:10px;border:1px solid #ddd;font-size:16px}
input{width:100%;margin:8px 0 12px} button{background:#111;color:#fff;border:0;cursor:pointer}
.msg{color:#c00;min-height:18px;margin-top:6px} .small{color:#666;font-size:12px;margin-top:10px}
</style>
<div class="wrap">
  <h1>🔒 Accès au guide</h1>
  <p>Entrez le <strong>mot de passe</strong> fourni par votre hôte.</p>
  <form method="POST">
    <input name="token" placeholder="Ex. TESTFR" required autofocus>
    <button type="submit">Continuer</button>
  </form>
  <div class="msg">{message}</div>
  <p class="small">FR · EN · IT · ES</p>
</div>
</html>"""

def _now(): return datetime.now(timezone.utc)
def _dt(s):  return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def _match(token: str):
    n = _now()
    for t in TOKENS:
        if t["token"] == token and _dt(t["start"]) <= n <= _dt(t["end"]):
            return t
    return None

def _html(msg=""): return Response(HTML.format(message=msg), mimetype="text/html; charset=utf-8")
def _go(lang=None): return redirect(f"{CARRD_URL}#{lang}" if lang else CARRD_URL, code=302)

@app.get("/")
def get_index():
    q = (request.args.get("token") or "").strip()
    if q:
        m = _match(q)
        return _go(m["lang"]) if m else _html("Lien expiré ou code invalide.")
    return _html()

@app.post("/")
def post_index():
    q = (request.form.get("token") or "").strip()
    m = _match(q)
    return _go(m["lang"]) if m else _html("Code invalide ou expiré.")
