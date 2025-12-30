from datetime import datetime, timezone
from flask import Flask, request, redirect, url_for, session, make_response
import html
import os
import re
from io import BytesIO
import base64
from string import Template
import qrcode
from qrcode.constants import ERROR_CORRECT_M

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ma-clé-ultra-secrète-1234567890")  # 👈 PASSE EN PRODUCTION

# ========= CONFIG =========
WIFI_SSID = "Linstant Roméon"
WIFI_PASS = "@Romeon13007"
WIFI_AUTH = "WPA"

APP_ADDRESS = "1 rue Turcon, 13007 Marseille"
MAPS_URL   = "https://www.google.com/maps/search/?api=1&query=1+rue+Turcon+13007+Marseille"
AIRBNB_URL = "https://www.airbnb.fr/rooms/1366485756382394689?guests=1&adults=1&s=67&unique_share_id=55c1ae1a-669d-45ae-a6b7-62f3e00fccc4"

TOKENS = [
    {"token": "Alessio", "lang": "fr", "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

# ========= HTML TEMPLATES =========
LOGIN_HTML = Template("""
<!doctype html>
<html lang="$lang"><meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Accès au guide – Instant Roméon</title>
<script src="https://cdn.tailwindcss.com"></script>
<body class="bg-slate-100 text-slate-800 p-8">
  <div class="max-w-xl mx-auto bg-white p-6 rounded-xl shadow">
    <h1 class="text-2xl font-semibold mb-4">🏡 Instant Roméon</h1>
    <p class="mb-4">Entrez le mot de passe fourni par votre hôte :</p>
    <form method="POST" class="space-y-4">
      <input name="token" placeholder="Ex. Marseille25" required autofocus
             class="w-full border px-4 py-2 rounded" />
      <button type="submit" class="w-full bg-blue-700 text-white px-4 py-2 rounded">Continuer</button>
    </form>
    <div class="mt-3 text-red-600 text-center">$message</div>
  </div>
</body>
</html>
""")

GUIDE_HTML = Template("""
<!doctype html>
<html lang="fr"><meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Guide – Instant Roméon</title>
<script src="https://cdn.tailwindcss.com"></script>
<body class="bg-slate-100 text-slate-800 p-8">
  <div class="max-w-3xl mx-auto bg-white p-6 rounded-xl shadow space-y-6">
    <h1 class="text-2xl font-semibold">🏡 Guide de l'appartement</h1>
    <p>Bienvenue à <b>l’Instant Roméon</b> !</p>
    <h2 class="text-xl font-semibold">📶 Wi-Fi</h2>
    <p>Réseau : <b>$ssid_h</b></p>
    <p>Mot de passe : <b>$pwd_h</b></p>
    <img src="data:image/png;base64,$qr_b64" alt="QR Wi-Fi" class="w-40 h-40 border p-2 rounded bg-white" />
    <p><a href="$airbnb" class="text-blue-700 underline" target="_blank">Voir l’annonce Airbnb</a></p>
    <p><a href="$maps" class="text-blue-700 underline" target="_blank">$address</a></p>
    <p><a href="$logout_url" class="text-sm text-gray-600 underline">Déconnexion</a></p>
  </div>
</body>
</html>
""")

# ========= UTILS =========
def _now_utc():
    return datetime.now(timezone.utc)

def _parse_iso(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def _token_valid(token):
    now = _now_utc()
    for t in TOKENS:
        if t["token"] == token:
            if _parse_iso(t["start"]) <= now <= _parse_iso(t["end"]):
                return t
    return None

def _html(s: str):
    resp = make_response(s)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

def _wifi_escape(value: str) -> str:
    return re.sub(r'([\\;,:"])', r'\\\1', value)

def _wifi_qr_text(ssid: str, pwd: str, auth: str) -> str:
    ssid_e = _wifi_escape(ssid)
    pwd_e  = _wifi_escape(pwd)
    auth_e = _wifi_escape(auth or "")
    return f"WIFI:T:{auth_e};S:{ssid_e};P:{pwd_e};;"

def _qr_png_base64(text: str, box_size: int = 6, border: int = 2) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")

# ========= ROUTES =========
@app.get("/")
def login_get():
    return _html(LOGIN_HTML.substitute(lang="fr", message=""))

@app.post("/")
def login_post():
    token = (request.form.get("token") or "").strip()
    match = _token_valid(token)
    if match:
        session["ok"] = True
        return redirect(url_for("guide"))
    return _html(LOGIN_HTML.substitute(lang="fr", message="Code invalide"))

@app.get("/guide")
def guide():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    wifi_text = _wifi_qr_text(WIFI_SSID, WIFI_PASS, WIFI_AUTH)
    qr_b64 = _qr_png_base64(wifi_text, box_size=6, border=1)
    html_out = GUIDE_HTML.substitute(
        logout_url=url_for("logout"),
        ssid_h=html.escape(WIFI_SSID),
        pwd_h=html.escape(WIFI_PASS),
        airbnb=AIRBNB_URL,
        maps=MAPS_URL,
        address=APP_ADDRESS,
        qr_b64=qr_b64
    )
    return _html(html_out)

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_get"))
