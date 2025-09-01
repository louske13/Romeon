# app.py — Portail sécurisé Airbnb Guide (Flask + Tailwind + PWA)

from datetime import datetime, timezone
from flask import (
    Flask, request, redirect, url_for, session,
    make_response, render_template
)

app = Flask(__name__)
app.secret_key = "change-moi-par-une-grosse-cle-secrete"

# ========= CONFIG =========
BG_URL   = "/static/images/bg.jpg"   # (optionnel) Image de fond, si tu veux t’en servir ailleurs
WIFI_SSID = "TON_SSID"
WIFI_PASS = "TON_MDP_WIFI"
WIFI_AUTH = "WPA"  # WEP | WPA | nopass

# Codes valides (tokens)
TOKENS = [
    {"token": "Marseille25", "lang": "fr",
     "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

# ========= HTML PAGES (inline) =========
LOGIN_HTML = """<!doctype html>
<html lang="{lang}">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Accès au guide – Instant Roméon</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-gradient-to-br from-[#eef2ff] via-[#f7f7fb] to-[#eaf5ff] text-slate-800">
  <div class="max-w-4xl mx-auto px-4 pt-10 pb-16">
    <!-- Intro -->
    <header class="text-center mb-8">
      <h1 class="text-3xl md:text-4xl font-semibold tracking-tight">🏡 Instant Roméon</h1>
      <p class="mt-3 text-slate-600 max-w-2xl mx-auto leading-relaxed">
        Merci d'avoir choisi <b>l’Instant Roméon</b> pour votre séjour. Je suis heureux de vous partager
        ce petit guide pratique – à la marseillaise – pour que votre voyage soit simple, doux… et mémorable.
      </p>
    </header>

    <!-- Carte login -->
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

      <div class="min-h-[22px] mt-3 text-center text-red-600">{message}</div>

      <div class="mt-4 text-center text-xs text-slate-500">
        Astuce : gardez cette page en favori sur votre écran d’accueil pour un accès rapide.
      </div>
    </div>
  </div>
</body>
</html>
"""

GUIDE_HTML = """<!doctype html>
<html lang="fr">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Guide – Instant Roméon</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-gradient-to-br from-[#eef2ff] via-[#f7f7fb] to-[#eaf5ff] text-slate-800">
  <div class="max-w-6xl mx-auto px-4 pt-8 pb-16">

    <!-- Barre top -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl md:text-3xl font-semibold">🏡 Guide de l’appartement</h1>
      <a href="{logout_url}" class="text-sm text-slate-600 hover:text-slate-900 underline">Déconnexion</a>
    </div>

    <!-- Intro -->
    <section class="mt-4 bg-white/90 backdrop-blur rounded-2xl shadow p-5 md:p-6">
      <p class="leading-relaxed text-slate-700">
        Bienvenue à <b>l’Instant Roméon</b> ! Ici, vous avez tout pour profiter de Marseille sans vous prendre la tête :
        Wi-Fi en un clic, bonnes adresses du quartier, idées de balades… Prenez le temps, respirez, et laissez-vous guider.
      </p>
    </section>

    <!-- Grille principale -->
    <section class="mt-6 grid md:grid-cols-2 gap-6">

      <!-- Carte Wi-Fi -->
      <div class="bg-white rounded-2xl shadow p-6">
        <h2 class="text-lg font-semibold">📶 Wi-Fi</h2>
        <p class="mt-1">Réseau : <b>{ssid}</b><br>Mot de passe : <b>{pwd}</b></p>
        <div id="wifi-qr" class="mt-4 flex items-center justify-center">
          <div id="qrbox" class="p-3 rounded-xl border border-slate-200"></div>
        </div>
        <div class="mt-3 text-xs text-slate-500 text-center">
          Scannez le QR code pour vous connecter automatiquement.
        </div>
      </div>

      <!-- Rubriques -->
      <div class="bg-white rounded-2xl shadow p-6">
        <h2 class="text-lg font-semibold">Rubriques</h2>
        <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <a href="/restaurants" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🍽️</span>
            <div>
              <div class="font-semibold group-hover:text-blue-700">Restaurants</div>
              <div class="text-xs text-slate-500">Mes spots à deux pas & vues mer</div>
            </div>
          </a>

          <a href="/visites" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🏛️</span>
            <div>
              <div class="font-semibold group-hover:text-blue-700">À visiter</div>
              <div class="text-xs text-slate-500">Bonnes idées autour de l’appart</div>
            </div>
          </a>

          <a href="/sorties" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🎶</span>
            <div>
              <div class="font-semibold group-hover:text-blue-700">Sorties</div>
              <div class="text-xs text-slate-500">Ambiance, musique & apéros</div>
            </div>
          </a>

          <!-- remplacé : Wi-Fi (détails) -> Commerces -->
          <a href="/commerces" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">🛒</span>
            <div>
              <div class="font-semibold group-hover:text-blue-700">Commerces utiles & incontournables</div>
              <div class="text-xs text-slate-500">Boulangeries, primeurs, supérettes, pharmacies…</div>
            </div>
          </a>
        </div>
      </div>

    </section>

    <!-- Footer -->
    <footer class="mt-8 text-center text-xs text-slate-500">
      Instant Roméon • Quartier d’Endoume • Marseille 7<sup>e</sup>
    </footer>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
  <script>
    const WIFI_TEXT = `WIFI:T:{auth};S:{ssid};P:{pwd};;`;
    new QRCode(document.getElementById("qrbox"), { text: WIFI_TEXT, width: 180, height: 180 });
  </script>
</body>
</html>
"""

# ========= UTIL & AUTH =========
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
    # Réponse HTML simple avec l’entête correct
    resp = make_response(s)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

# ========= ROUTES =========
@app.get("/")
def login_get():
    return _html(LOGIN_HTML.format(bg_url=BG_URL, message="", lang="fr"))

@app.post("/")
def login_post():
    token = (request.form.get("token") or "").strip()
    match = _token_valid(token)
    if match:
        session["ok"] = True
        return redirect(url_for("guide"))
    return _html(LOGIN_HTML.format(bg_url=BG_URL, message="Code invalide", lang="fr"))

@app.get("/guide")
def guide():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return _html(GUIDE_HTML.format(
        bg_url=BG_URL,
        logout_url=url_for("logout"),
        ssid=WIFI_SSID, pwd=WIFI_PASS, auth=WIFI_AUTH
    ))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_get"))

# ------- RUBRIQUES (templates) -------
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

# (garde /wifi si tu as un template wifi.html, sinon tu peux le supprimer)
@app.get("/wifi")
def wifi():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    return render_template("wifi.html")

# ------- PWA -------
@app.get("/manifest.webmanifest")
def manifest():
    return make_response(
        """{"name":"Guide","short_name":"Guide","start_url":"/",
"display":"standalone","background_color":"#0b1736","theme_color":"#0b1736"}""",
        200,
        {"Content-Type": "application/manifest+json"}
    )

@app.get("/service-worker.js")
def sw():
    return make_response("self.addEventListener('fetch', e=>{});", 200, {"Content-Type": "text/javascript"})
