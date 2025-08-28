# app.py — Portail mot de passe -> redirection vers Carrd (Render)
from datetime import datetime, timezone
from flask import Flask, request, redirect, Response

app = Flask(__name__)

# 👉 REMPLACE par ton URL Carrd (ex: "https://tonsite.carrd.co")
CARRD_URL = "https://ton-site.carrd.co"

# 👉 TOKENS (exemples). Ajoute une ligne par séjour.
# Les dates sont en UTC; mets large pour tester.
TOKENS = [
    {"token": "TESTFR", "lang": "fr", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
    {"token": "TESTEN", "lang": "en", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
    # {"token": "Baptiste4", "lang": "fr", "start": "2025-08-26T00:00:00Z", "end": "2025-08-30T23:59:59Z"},
]

# ====== PAGE HTML (fond d'écran + styles propres) ======
HTML = """<!doctype html>
<html lang="fr">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accès guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after{{ box-sizing:border-box; }}
  @keyframes fadeIn {{ from {{opacity:0}} to {{opacity:1}} }}
  @keyframes floatUp {{ from {{opacity:0; transform:translateY(12px)}} to {{opacity:1; transform:none}} }}

  body{{ 
    font-family:'Poppins',system-ui,Segoe UI,Roboto,Arial,sans-serif;
    background: url("https://png.pngtree.com/thumb_back/fh260/background/20230323/pngtree-marseille-old-port-and-fort-saint-jean-and-museum-of-european-photo-image_2100164.jpg") no-repeat center center fixed;
    background-size: cover;
    margin: 0;
  }}
  .overlay{{ position:fixed; inset:0; background:rgba(0,0,0,.55); animation:fadeIn .6s ease-out both; }}

  .wrap{{ 
    position:relative;
    width:min(520px, calc(100% - 32px));
    margin:10vh auto;
    background:rgba(255,255,255,0.94);
    padding:24px;
    border-radius:16px;
    box-shadow:0 14px 40px rgba(0,0,0,.18);
    text-align:center;                 /* ← centrage du contenu */
    animation:floatUp .6s .1s ease-out both;   /* ← fondu + léger slide */
  }}

  h1{{ font-size:22px; margin:0 0 8px; display:flex; align-items:center; gap:8px; justify-content:center; }}
  p{{ margin:0 0 14px; color:#444; }}

  .field{{ margin-top:6px; }}
  input{{ 
    display:block; width:100%;
    padding:14px 16px; 
    border-radius:12px; 
    border:2px solid #e5e7eb; 
    font-size:16px; 
    outline:none; 
    background:#fff;
    margin-inline:auto;
  }}
  input:focus{{ border-color:#0078ff; box-shadow:0 0 0 3px rgba(0,120,255,.12); }}

  .actions{{ margin-top:12px; display:flex; justify-content:center; }}  /* ← bouton au centre */
  button[type=submit]{{ 
    background:#004080; 
    color:#fff; 
    border:0; 
    padding:12px 18px; 
    border-radius:12px; 
    font-weight:600; 
    cursor:pointer; 
    transition:transform .04s ease, opacity .15s ease, box-shadow .15s;
  }}
  button[type=submit]:hover{{ opacity:.95; box-shadow:0 6px 14px rgba(0,64,128,.25); }}
  button[type=submit]:active{{ transform:translateY(1px); }}

  .msg{{ color:#c00; min-height:18px; margin-top:8px; }}
</style>

<div class="overlay"></div>

<div class="wrap">
  <h1>🔒 Accès au guide</h1>
  <p>Entrez <strong>le mot de passe</strong> fourni par votre hôte.</p>

  <form method="POST" class="field">
    <input name="token" placeholder="Ex. TESTFR" required autofocus>
    <div class="actions">
      <button type="submit">Continuer</button>
    </div>
  </form>

  <div class="msg">{message}</div>
</div>
</html>"""

# ====== LOGIQUE PY ======
def _now_utc():
    return datetime.now(timezone.utc)

def _parse_iso(iso_str: str):
    # format attendu: 'YYYY-MM-DDTHH:MM:SSZ'
    try:
        return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        # en cas de format foireux, on renvoie "toujours valide" pour éviter un 500
        return datetime.min.replace(tzinfo=timezone.utc)

def _find_match(token: str):
    now = _now_utc()
    for t in TOKENS:
        if t.get("token") == token:
            start = _parse_iso(t.get("start", "1970-01-01T00:00:00Z"))
            end   = _parse_iso(t.get("end",   "2999-12-31T23:59:59Z"))
            if start <= now <= end:
                return t
    return None

def _html(message: str = "") -> Response:
    return Response(HTML.format(message=message), mimetype="text/html; charset=utf-8")

def _go(lang: str | None):
    # si tu n'utilises pas les ancres de langue, on ignore "lang" et on va juste sur la page
    return redirect(CARRD_URL, code=302)

@app.get("/")
def get_index():
    # Permet aussi /?token=Baptiste4 pour auto-rediriger
    token = (request.args.get("token") or "").strip()
    if token:
        m = _find_match(token)
        return _go(m.get("lang") if m else None) if m else _html("Lien expiré ou code invalide.")
    return _html()

@app.post("/")
def post_index():
    token = (request.form.get("token") or "").strip()
    m = _find_match(token)
    return _go(m.get("lang") if m else None) if m else _html("Code invalide ou expiré.")
