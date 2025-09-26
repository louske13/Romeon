from datetime import datetime, timezone
from flask import (
    Flask, request, redirect, url_for, session,
    make_response, render_template
)
import html
import os
import re
from io import BytesIO
import base64
from string import Template
import qrcode
from qrcode.constants import ERROR_CORRECT_M

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-moi-par-une-grosse-cle-secrete")

# ========= CONFIG =========
WIFI_SSID = "Linstant Roméon"
WIFI_PASS = "@Romeon13007"
WIFI_AUTH = "WPA"

APP_ADDRESS = "1 rue Turcon, 13007 Marseille"
MAPS_URL   = "https://www.google.com/maps/search/?api=1&query=1+rue+Turcon+13007+Marseille"
AIRBNB_URL = "https://www.airbnb.fr/rooms/1366485756382394689?guests=1&adults=1&s=67&unique_share_id=55c1ae1a-669d-45ae-a6b7-62f3e00fccc4"

TOKENS = [
    {"token": "Maria", "lang": "fr",
     "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

# ========= HTML =========
LOGIN_HTML = Template("""<!doctype html>
<html lang="$lang">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Accès au guide – Instant Roméon</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<link rel="manifest" href="/static/manifest.webmanifest">
<meta name="theme-color" content="#0b1736">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-gradient-to-br from-[#eef2ff] via-[#f7f7fb] to-[#eaf5ff] text-slate-800">
  <div class="max-w-4xl mx-auto px-4 pt-10 pb-16">
    <header class="text-center mb-8">
      <h1 class="text-3xl md:text-4xl font-semibold tracking-tight">🏡 Instant Roméon</h1>
      <p class="mt-3 text-slate-600 max-w-2xl mx-auto leading-relaxed">
        Merci d'avoir choisi <b>l’Instant Roméon</b>. Ce petit guide pratique va vous simplifier la vie.
      </p>
    </header>

    <div class="mx-auto max-w-xl bg-white/90 backdrop-blur rounded-2xl shadow-2xl p-6 md:p-8">
      <h2 class="text-xl md:text-2xl font-semibold text-slate-900">🔒 Accès au guide</h2>
      <p class="mt-2 text-slate-600">Entrez le mot de passe fourni par votre hôte :</p>

      <form method="POST" class="mt-5 space-y-4">
        <input name="token" placeholder="Ex. Marseille25" required autofocus
               class="w-full rounded-xl border-2 border-slate-200 focus:border-blue-700 px-4 py-3 outline-none transition" />
        <button type="submit"
                class="w-full rounded-xl bg-blue-700 hover:bg-blue-800 text-white px-5 py-3 font-semibold shadow">
          Continuer
        </button>
      </form>

      <div class="min-h-[22px] mt-3 text-center text-red-600">$message</div>
      <div class="mt-4 text-center text-xs text-slate-500">Astuce : vous pourrez l’installer comme une application.</div>
    </div>
  </div>
  <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js');
    }
  </script>
</body>
</html>
""")

GUIDE_HTML = Template("""<!doctype html>
<html lang="fr">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Guide – Instant Roméon</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<link rel="manifest" href="/static/manifest.webmanifest">
<meta name="theme-color" content="#0b1736">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-gradient-to-br from-[#eef2ff] via-[#f7f7fb] to-[#eaf5ff] text-slate-800">
  <div class="max-w-6xl mx-auto px-4 pt-8 pb-16">

    <div class="flex items-center justify-between gap-4 flex-wrap">
      <h1 class="text-2xl md:text-3xl font-semibold">🏡 Guide de l’appartement</h1>
      <div class="flex items-center gap-3">
        <a href="$airbnb" target="_blank"
           class="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-white px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-50 shadow-sm">
          🏠 Voir l’annonce Airbnb
        </a>
        <a href="$logout_url" class="text-sm text-slate-600 hover:text-slate-900 underline">Déconnexion</a>
      </div>
    </div>

    <section class="mt-4 bg-white/90 backdrop-blur rounded-2xl shadow p-5 md:p-6">
      <p class="leading-relaxed text-slate-700">
        Bienvenue à <b>l’Instant Roméon</b> ! Wi-Fi en un clic, bonnes adresses, idées de balades… laissez-vous guider.
      </p>
    </section>

    <section class="mt-6 grid md:grid-cols-2 gap-6">
      <div class="bg-white rounded-2xl shadow p-6">
        <h2 class="text-lg font-semibold mb-3">📶 Wi-Fi</h2>
        <div class="grid md:grid-cols-2 gap-4 items-center">
          <div class="text-[15px]">
            <div>Réseau : <b>$ssid_h</b></div>
            <div>Mot de passe : <b>$pwd_h</b></div>
            <div class="mt-3 text-xs text-slate-500">Scannez le QR code pour vous connecter automatiquement.</div>
          </div>
          <div class="flex justify-center md:justify-end">
            <img src="data:image/png;base64,$qr_b64"
                 alt="QR Wi-Fi"
                 class="p-3 rounded-xl border border-slate-200 w-[180px] h-[180px] bg-white" />
          </div>
        </div>

        <!-- Bouton Installer l’app -->
        <div class="mt-6 text-center">
          <button id="installAppBtn"
            class="rounded-xl bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 text-sm font-semibold shadow">
            📲 Télécharger l’application
          </button>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow p-6">
        <h2 class="text-lg font-semibold">Rubriques</h2>
        <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <a href="/restaurants" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🍽️</span>
            <div><div class="font-semibold group-hover:text-blue-700">Restaurants</div><div class="text-xs text-slate-500">Mes spots à deux pas & vues mer</div></div>
          </a>
          <a href="/visites" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🏛️</span>
            <div><div class="font-semibold group-hover:text-blue-700">À visiter</div><div class="text-xs text-slate-500">Bonnes idées autour de l’appart</div></div>
          </a>
          <a href="/sorties" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🎶</span>
            <div><div class="font-semibold group-hover:text-blue-700">Sorties</div><div class="text-xs text-slate-500">Ambiance, musique & apéros</div></div>
          </a>
          <a href="/commerces" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🛍️</span>
            <div><div class="font-semibold group-hover:text-blue-700">Commerces utiles</div><div class="text-xs text-slate-500">Artisans & incontournables du quartier</div></div>
          </a>
          <a href="$maps" target="_blank" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">📍</span>
            <div><div class="font-semibold group-hover:text-blue-700">Localisation</div><div class="text-xs text-slate-500">$address</div></div>
          </a>
          <a href="/numeros" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">☎️</span>
            <div><div class="font-semibold group-hover:text-blue-700">Numéros utiles</div><div class="text-xs text-slate-500">Urgences & contacts du quartier</div></div>
          </a>
        </div>
      </div>
    </section>

    <footer class="mt-8 text-center text-xs text-slate-500">
      Instant Roméon • Quartier d’Endoume • Marseille 7<sup>e</sup>
    </footer>
  </div>

  <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js');
    }

    let deferredPrompt;
    const installBtn = document.getElementById('installAppBtn');
    installBtn.style.display = 'none';

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      installBtn.style.display = 'inline-flex';
    });

    installBtn.addEventListener('click', async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        await deferredPrompt.userChoice;
        deferredPrompt = null;
        installBtn.style.display = 'none';
      } else {
        alert("ℹ️ Pour installer sur iPhone :\\n1. Bouton Partager (carré + flèche)\\n2. Choisissez 'Sur l’écran d’accueil'");
      }
    });
  </script>
</body>
</html>
""")

# ========= Utils =========
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

# ========= Routes =========
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

# ------- Rubriques -------
@app.get("/restaurants")
def restaurants():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return render_template("restaurants.html")

@app.get("/visites")
def visites():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return render_template("visites.html")

@app.get("/sorties")
def sorties():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return render_template("sorties.html")

@app.get("/commerces")
def commerces():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return render_template("commerces.html")

@app.get("/numeros")
def numeros():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return render_template("numeros.html")

# ------- PWA: service worker -------
@app.get("/service-worker.js")
def sw():
    js = (
        "self.addEventListener('install', e=>self.skipWaiting());"
        "self.addEventListener('activate', e=>self.clients.claim());"
        "self.addEventListener('fetch', e=>{});"
    )
    return make_response(js, 200, {"Content-Type": "text/javascript"})
