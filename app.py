# app.py — Portail mot de passe -> redirection vers Carrd (version robuste)
from datetime import datetime, timezone
from flask import Flask, request, redirect, Response

app = Flask(__name__)

# ⚠️ REMPLACE par ton URL Carrd (ex: "https://tonsite.carrd.co")
CARRD_URL = "https://ton-site.carrd.co"

# Tokens de test (valables longtemps)
TOKENS = [
    {"token": "TESTFR", "lang": "fr", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
    {"token": "TESTEN", "lang": "en", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

HTML = """<!doctype html>
<html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accès guide</title>
<style>
  body{{ 
    font-family: system-ui,Segoe UI,Roboto,Arial,sans-serif;
    background: url("https://png.pngtree.com/thumb_back/fh260/background/20230323/pngtree-marseille-old-port-and-fort-saint-jean-and-museum-of-european-photo-image_2100164.jpg") no-repeat center center fixed;
    background-size: cover;
    margin: 0;
  }}
  .overlay{{position: fixed; inset: 0; background: rgba(0, 0, 0, 0.35);}}
  .wrap{{position: relative; max-width: 520px; margin: 10vh auto; background: rgba(255,255,255,0.94); padding: 24px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);}}
  h1{{font-size: 22px; margin: 0 0 10px;}}
  p{{margin: 0 0 14px; color: #444;}}
  input, button[type=submit]{{padding: 12px 14px; border-radius: 10px; border: 1px solid #ddd; font-size: 16px;}}
  input{{width: 100%; margin: 8px 0 12px;}}
  button[type=submit]{{background: #111; color: #fff; border: 0; cursor: pointer;}}
  .msg{{color: #c00; min-height: 18px; margin-top: 6px;}}
</style>
<div class="overlay"></div>
<div class="wrap">
  <h1>🔒 Accès au guide</h1>
  <p>Entrez le <strong>mot de passe</strong> fourni par votre hôte.</p>
  <form method="POST">
    <input name="token" placeholder="Ex. TESTFR" required autofocus>
    <button type="submit">Continuer</button>
  </form>
  <div class="msg">{message}</div>
</div>
</html>"""





def _now_utc():
    return datetime.now(timezone.utc)

def _parse_iso(iso_str):
    # Accepte 'YYYY-MM-DDTHH:MM:SSZ'
    try:
        return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        # Si mauvais format, on considère "toujours valide" pour éviter un 500
        return datetime.min.replace(tzinfo=timezone.utc)

def _find_match(token):
    now = _now_utc()
    for t in TOKENS:
        if t.get("token") == token:
            start = _parse_iso(t.get("start", "1970-01-01T00:00:00Z"))
            end   = _parse_iso(t.get("end",   "2999-12-31T23:59:59Z"))
            if start <= now <= end:
                return t
    return None

def _html(message=""):
    return Response(HTML.format(message=message), mimetype="text/html; charset=utf-8")

def _go(lang):
    try:
        url = f"{CARRD_URL}#{lang}" if lang else CARRD_URL
        return redirect(url, code=302)
    except Exception:
        return _html("Erreur de redirection. Vérifiez l'URL du guide.")

@app.get("/")
def get_index():
    token = (request.args.get("token") or "").strip()
    if token:
        m = _find_match(token)
        return _go(m.get("lang")) if m else _html("Lien expiré ou code invalide.")
    return _html()

@app.post("/")
def post_index():
    token = (request.form.get("token") or "").strip()
    m = _find_match(token)
    return _go(m.get("lang")) if m else _html("Code invalide ou expiré.")
