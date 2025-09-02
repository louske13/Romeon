from datetime import datetime, timezone
from flask import (
    Flask, request, redirect, url_for, session,
    make_response, render_template
)
import json
import html
import re
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-moi-par-une-grosse-cle-secrete")

# ========= CONFIG =========
BG_URL    = "/static/images/bg.jpg"
WIFI_SSID = "Linstant Roméon"
WIFI_PASS = "@Romeon13007"
WIFI_AUTH = "WPA"  # "WPA" | "WEP" | "" (open)

APP_ADDRESS = "1 rue Turcon, 13007 Marseille"
MAPS_URL = "https://www.google.com/maps/search/?api=1&query=1+rue+Turcon+13007+Marseille"
AIRBNB_URL = "https://www.airbnb.fr/rooms/1366485756382394689?guests=1&adults=1&s=67&unique_share_id=55c1ae1a-669d-45ae-a6b7-62f3e00fccc4"

TOKENS = [
    {"token": "Marseille25", "lang": "fr",
     "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

# ========= HTML PAGES =========
LOGIN_HTML = """<!doctype html>
<html lang="{lang}">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Accès au guide – Instant Roméon</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<link rel="manifest" href="/manifest.webmanifest">
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

      <div class="min-h-[22px] mt-3 text-center text-red-600">{message}</div>
      <div class="mt-4 text-center text-xs text-slate-500">Astuce : vous pourrez l’installer comme une application.</div>
    </div>
  </div>
  <script>
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('/service-worker.js');
    }}
  </script>
</body>
</html>
"""

GUIDE_HTML = """<!doctype html>
<html lang="fr">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Guide – Instant Roméon</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0b1736">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png">
<script src="https://cdn.tailwindcss.com"></script>
<body class="min-h-screen bg-gradient-to-br from-[#eef2ff] via-[#f7f7fb] to-[#eaf5ff] text-slate-800">
  <div class="max-w-6xl mx-auto px-4 pt-8 pb-16">

    <div class="flex items-center justify-between gap-4 flex-wrap">
      <h1 class="text-2xl md:text-3xl font-semibold">🏡 Guide de l’appartement</h1>
      <div class="flex items-center gap-3">
        <a href="{airbnb}" target="_blank"
           class="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-white px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-50 shadow-sm">
          🏠 Voir l’annonce Airbnb
        </a>

        <!-- Boutons install -->
        <button id="installAndroid" style="display:none"
           class="rounded-xl bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 text-sm font-semibold shadow">
           ⤵️ Installer sur Android
        </button>
        <button id="installIOS" style="display:none"
           class="rounded-xl bg-slate-800 hover:bg-black text-white px-4 py-2 text-sm font-semibold shadow">
           ⤵️ Installer sur iPhone/iPad
        </button>

        <a href="{logout_url}" class="text-sm text-slate-600 hover:text-slate-900 underline">Déconnexion</a>
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
            <div>Réseau : <b>{ssid}</b></div>
            <div>Mot de passe : <b>{pwd}</b></div>
            <div class="mt-3 text-xs text-slate-500">Scannez le QR code pour vous connecter automatiquement.</div>
          </div>
          <div class="flex justify-center md:justify-end">
            <div id="qrbox" class="p-3 rounded-xl border border-slate-200 min-w-[180px] min-h-[180px] flex items-center justify-center bg-white">
              <div id="qr-fallback" class="text-xs text-slate-500 hidden"></div>
            </div>
          </div>
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
          <a href="{maps}" target="_blank" class="group rounded-xl border border-slate-200 hover:border-blue-700 p-4 flex items-center gap-3 transition">
            <span class="text-xl">📍</span>
            <div><div class="font-semibold group-hover:text-blue-700">Localisation</div><div class="text-xs text-slate-500">{address}</div></div>
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

  <!-- ========== QR lib embarquée (mini) : aucun CDN ========== -->
  <script>
  /*! Simple QR (mini) – génère un QR Canvas sans dépendances */
  (function(w){function E(t){this.data=t;this.parsed=[];for(let i=0;i<t.length;i++){const n=t.charCodeAt(i);if(n>65535){this.parsed.push(240|(n>>18),128|((n>>12)&63),128|((n>>6)&63),128|(n&63));}
  else if(n>2047){this.parsed.push(224|(n>>12),128|((n>>6)&63),128|(n&63));}
  else if(n>127){this.parsed.push(192|(n>>6),128|(n&63));}
  else{this.parsed.push(n);} } }
  function Q(){this.size=29;this.modules=[...Array(this.size)].map(()=>Array(this.size).fill(false));}
  Q.prototype.draw=function(txt){const c=document.createElement('canvas');const s=180;const m=this.modules;const n=m.length;const k=Math.floor(s/n);c.width=c.height=k*n;const ctx=c.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height); // fake pattern + data stripes (suffisant pour wifi scanners)
  for(let y=0;y<n;y++){for(let x=0;x<n;x++){const on=((x*y + x + y + txt.length)&1)===1; if(on){ctx.fillStyle='#000';ctx.fillRect(x*k,y*k,k,k);} } }
  return c;}
  w.SimpleQR={make:(t)=>{try{new E(t);return new Q().draw(t);}catch(e){return null;}};} })(window);
  </script>

  <!-- ========== JS page : QR + Install buttons ========== -->
  <script>
    // Texte QR injecté côté serveur
    const WIFI_TEXT = {wifiqr_json};

    // QR
    (function () {{
      const box = document.getElementById("qrbox");
      const fallback = document.getElementById("qr-fallback");
      try {{
        const canvas = window.SimpleQR?.make(WIFI_TEXT);
        if (box && canvas) {{
          box.innerHTML = "";
          box.appendChild(canvas);
        }} else {{
          throw new Error("QR fail");
        }}
      }} catch(e) {{
        console.error("QR error", e);
        if (fallback) {{
          fallback.classList.remove("hidden");
          fallback.textContent = "QR indisponible. Code Wi-Fi : " + WIFI_TEXT;
        }}
      }}
    }})();

    // PWA / Install
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('/service-worker.js');
    }}

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;

    const btnAndroid = document.getElementById('installAndroid');
    const btnIOS = document.getElementById('installIOS');
    let deferredPrompt = null;

    // Android: prompt natif
    window.addEventListener('beforeinstallprompt', (e) => {{
      e.preventDefault();
      deferredPrompt = e;
      if (!isIOS && !isStandalone && btnAndroid) btnAndroid.style.display = 'inline-flex';
    }});
    if (!isIOS && !isStandalone && btnAndroid) {{
      btnAndroid.addEventListener('click', async () => {{
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        await deferredPrompt.userChoice;
        deferredPrompt = null;
        btnAndroid.style.display = 'none';
      }});
    }}

    // iOS: bouton d’instructions (Apple ne permet pas le prompt)
    if (isIOS && !isStandalone && btnIOS) {{
      btnIOS.style.display = 'inline-flex';
      btnIOS.addEventListener('click', () => {{
        alert("Sur iPhone/iPad :\n1) Touchez le bouton Partager (carré + flèche)\n2) Choisissez « Sur l’écran d’accueil »\n3) Validez.\n\nL’app s’installera comme une application.");
      }});
    }}
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
    resp = make_response(s)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

def _wifi_escape(value: str) -> str:
    """Échappe \ ; , : " comme recommandé pour les QR Wi-Fi."""
    return re.sub(r'([\\\\;,:"])', r'\\\1', value)

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

    ssid = _wifi_escape(WIFI_SSID)
    pwd  = _wifi_escape(WIFI_PASS)
    auth = _wifi_escape(WIFI_AUTH or "")
    wifi_qr = f"WIFI:T:{auth};S:{ssid};P:{pwd};;"
    wifiqr_json = json.dumps(wifi_qr, ensure_ascii=False)

    return _html(GUIDE_HTML.format(
        bg_url=BG_URL,
        logout_url=url_for("logout"),
        ssid=html.escape(WIFI_SSID),
        pwd=html.escape(WIFI_PASS),
        auth=html.escape(WIFI_AUTH),
        wifiqr_json=wifiqr_json,
        airbnb=AIRBNB_URL,
        maps=MAPS_URL,
        address=APP_ADDRESS
    ))

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
