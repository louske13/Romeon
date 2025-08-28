# app.py — Portail sécurisé Airbnb Guide (Flask + Tailwind + PWA)
from datetime import datetime, timezone
from flask import Flask, request, redirect, Response, session, url_for

app = Flask(__name__)
app.secret_key = "change-moi-par-une-grosse-cle-secrete"

# ========= CONFIG =========
BG_URL = "/static/images/bg.jpg"   # Image de fond
WIFI_SSID = "TON_SSID"
WIFI_PASS = "TON_MDP_WIFI"
WIFI_AUTH = "WPA"

# Codes valides (tokens)
TOKENS = [
    {"token": "Marseille25", "lang": "fr",
     "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

# ========= HTML PAGES =========
LOGIN_HTML = """<!doctype html>
<html lang="{lang}">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Accès au guide</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-cover bg-center" style="background-image:url('{bg_url}')">
  <div class="fixed inset-0 bg-black/60"></div>
  <div class="relative mx-auto max-w-xl px-4 mt-28 bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-6 text-center">
    <h1 class="text-2xl font-semibold">🔒 Accès au guide</h1>
    <p class="mt-2 text-slate-600">Entrez le mot de passe fourni par votre hôte :</p>
    <form method="POST" class="mt-5">
      <input name="token" placeholder="Ex. Marseille25" required autofocus
             class="w-full rounded-xl border-2 border-slate-200 focus:border-blue-600 px-4 py-3"/>
      <div class="mt-4 flex justify-center">
        <button type="submit"
                class="rounded-xl bg-blue-900 text-white px-5 py-3 font-semibold shadow hover:shadow-lg">
          Continuer
        </button>
      </div>
    </form>
    <div class="min-h-[20px] mt-2 text-red-600">{message}</div>
  </div>
</body>
</html>
"""

GUIDE_HTML = """<!doctype html>
<html lang="fr">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Guide</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-cover bg-center" style="background-image:url('{bg_url}')">
  <div class="fixed inset-0 bg-black/60"></div>
  <header class="relative max-w-5xl mx-auto px-4 pt-6 flex items-center justify-between text-white">
    <h1 class="text-xl md:text-2xl font-semibold">🏡 Guide de l’appartement</h1>
    <a href="{logout_url}" class="text-white/90 hover:text-white underline">Déconnexion</a>
  </header>

  <main class="relative max-w-5xl mx-auto px-4 pb-20">
    <section class="mt-6 grid md:grid-cols-2 gap-6">
      <!-- Wi-Fi -->
      <div class="bg-white/95 rounded-2xl shadow-2xl p-6">
        <h2 class="text-lg font-semibold">Wi-Fi</h2>
        <p>Réseau : <b>{ssid}</b><br>Mot de passe : <b>{pwd}</b></p>
        <div id="wifi-qr" class="mt-3"></div>
      </div>

      <!-- Rubriques -->
      <div class="bg-white/95 rounded-2xl shadow-2xl p-6">
        <h2 class="text-lg font-semibold">Rubriques</h2>
        <div class="grid grid-cols-2 gap-4 mt-3">
          <a href="/restaurants" class="bg-slate-100 rounded-xl p-3 text-center hover:bg-slate-200">
            🍽️ Restaurants
          </a>
          <a href="/visites" class="bg-slate-100 rounded-xl p-3 text-center hover:bg-slate-200">
            🏛️ À visiter
          </a>
          <a href="/sorties" class="bg-slate-100 rounded-xl p-3 text-center hover:bg-slate-200">
            🎶 Sorties
          </a>
        </div>
      </div>
    </section>
  </main>

<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>
  const WIFI_TEXT = `WIFI:T:{auth};S:{ssid};P:{pwd};;`;
  new QRCode(document.getElementById("wifi-qr"), {{
    text: WIFI_TEXT, width: 180, height: 180
  }});
</script>
</body>
</html>
"""

RESTAURANTS_HTML = f"""<!doctype html>
<html><body style="background:url('{BG_URL}');background-size:cover">
<div style="background:rgba(255,255,255,0.9);margin:40px auto;max-width:700px;padding:20px;border-radius:16px">
<h1>🍽️ Bons plans restaurants</h1>
<h2>Chez Fonfon</h2>
<p>Spécialité bouillabaisse · Vieux-Port.</p>
<a href="https://goo.gl/maps/xxxx" target="_blank">Voir sur Google Maps</a>
<h2>La Caravelle</h2>
<p>Bar-restaurant avec vue sur le port et ambiance jazz.</p>
<a href="https://goo.gl/maps/yyyy" target="_blank">Voir sur Google Maps</a>
</div></body></html>
"""

VISITES_HTML = f"""<!doctype html>
<html><body style="background:url('{BG_URL}');background-size:cover">
<div style="background:rgba(255,255,255,0.9);margin:40px auto;max-width:700px;padding:20px;border-radius:16px">
<h1>🏛️ Lieux à visiter</h1>
<h2>Notre-Dame de la Garde</h2>
<p>Emblème de Marseille avec vue panoramique.</p>
<a href="https://goo.gl/maps/xxxx" target="_blank">Voir sur Google Maps</a>
<h2>Calanques de Sormiou</h2>
<p>Site naturel exceptionnel.</p>
<a href="https://goo.gl/maps/yyyy" target="_blank">Voir sur Google Maps</a>
</div></body></html>
"""

SORTIES_HTML = f"""<!doctype html>
<html><body style="background:url('{BG_URL}');background-size:cover">
<div style="background:rgba(255,255,255,0.9);margin:40px auto;max-width:700px;padding:20px;border-radius:16px">
<h1>🎶 Sorties & activités</h1>
<h2>Dock des Suds</h2>
<p>Lieu incontournable pour concerts et soirées.</p>
<a href="https://goo.gl/maps/xxxx" target="_blank">Voir sur Google Maps</a>
<h2>Cours Julien</h2>
<p>Quartier animé avec bars, street-art et musique live.</p>
<a href="https://goo.gl/maps/yyyy" target="_blank">Voir sur Google Maps</a>
</div></body></html>
"""

# ========= LOGIQUE =========
def _now_utc(): return datetime.now(timezone.utc)
def _parse_iso(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def _token_valid(token):
    now = _now_utc()
    for t in TOKENS:
        if t["token"] == token:
            if _parse_iso(t["start"]) <= now <= _parse_iso(t["end"]):
                return t
    return None

def _html(s): return Response(s, mimetype="text/html; charset=utf-8")

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
    return _html(GUIDE_HTML.format(bg_url=BG_URL, logout_url=url_for("logout"),
                                   ssid=WIFI_SSID, pwd=WIFI_PASS, auth=WIFI_AUTH))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_get"))

# Nouvelles pages
@app.get("/restaurants")
def restaurants(): return _html(RESTAURANTS_HTML)

@app.get("/visites")
def visites(): return _html(VISITES_HTML)

@app.get("/sorties")
def sorties(): return _html(SORTIES_HTML)

# PWA fichiers
@app.get("/manifest.webmanifest")
def manifest():
    return Response("""{"name":"Guide","short_name":"Guide","start_url":"/",
"display":"standalone","background_color":"#0b1736","theme_color":"#0b1736"}""",
    mimetype="application/manifest+json")

@app.get("/service-worker.js")
def sw():
    return Response("self.addEventListener('fetch', e=>{});", mimetype="text/javascript")
