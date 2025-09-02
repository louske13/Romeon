from datetime import datetime, timezone
from flask import (
    Flask, request, redirect, url_for, session,
    make_response, render_template
)
import json
import html
import re

app = Flask(__name__)
app.secret_key = "change-moi-par-une-grosse-cle-secrete"

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
        <button id="installBtn" style="display:none"
           class="rounded-xl bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 text-sm font-semibold shadow">
           ⤵️ Installer l’app
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
            <div id="qrbox" class="p-3 rounded-xl border border-slate-200 min-w-[180px] min-h-[180px] flex items-center justify-center">
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

  <!-- QR lib embarquée (QRCodeJS minifié) -->
  <script>
  /* qrcode.js (min) – embarqué pour éviter tout blocage CDN */
  !function(o){function u(a){this.mode=c.MODE_8BIT_BYTE,this.data=a,this.parsedData=[];for(var t=0,e=this.data.length;t<e;t++){var r=[],n=this.data.charCodeAt(t);n>65536?(r[0]=240|(1835008&n)>>>18,r[1]=128|(258048&n)>>>12,r[2]=128|(4032&n)>>>6,r[3]=128|63&n):2048<n?(r[0]=224|(61440&n)>>>12,r[1]=128|(4032&n)>>>6,r[2]=128|63&n):128<n?(r[0]=192|(1984&n)>>>6,r[1]=128|63&n):r[0]=n,this.parsedData.push(r)}this.parsedData=Array.prototype.concat.apply([],this.parsedData)}function i(a,t){this.typeNumber=a,this.errorCorrectLevel=t,this.modules=null,this.moduleCount=0,this.dataCache=null,this.dataList=[]}var c={PAD0:236,PAD1:17,MODE_NUMBER:1,MODE_ALPHA_NUM:2,MODE_8BIT_BYTE:4,MODE_KANJI:8},s={L:1,M:0,Q:3,H:2};u.prototype={getLength:function(){return this.parsedData.length},write:function(a){for(var t=0,e=this.parsedData.length;t<e;t++)a.put(this.parsedData[t],8)}},i.prototype={addData:function(a){this.dataList.push(new u(a)),this.dataCache=null},isDark:function(a,t){if(null==this.modules||a<0||this.moduleCount<=a||t<0||this.moduleCount<=t)throw new Error(a+","+t);return this.modules[a][t]},getModuleCount:function(){return this.moduleCount},make:function(){if(this.typeNumber<1)this.typeNumber=1;for(;this.typeNumber<41&&!this.isMakeable();)this.typeNumber++;this.makeImpl(!1,this.getBestMaskPattern())},isMakeable:function(){var a=this.createData(this.typeNumber,s.M);return a.length>0},makeImpl:function(a,t){this.moduleCount=4*this.typeNumber+17,this.modules=new Array(this.moduleCount);for(var e=0;e<this.moduleCount;e++){this.modules[e]=new Array(this.moduleCount);for(var r=0;r<this.moduleCount;r++)this.modules[e][r]=null}this.setupPositionProbePattern(0,0),this.setupPositionProbePattern(this.moduleCount-7,0),this.setupPositionProbePattern(0,this.moduleCount-7),this.setupTimingPattern(),this.setupTypeInfo(a,t),this.dataCache=this.createData(this.typeNumber,s.M),this.mapData(this.dataCache,t)},setupPositionProbePattern:function(a,t){for(var e=-1;e<=7;e++)if(!(a+e<=-1||this.moduleCount<=a+e))for(var r=-1;r<=7;r++)t+r<=-1||this.moduleCount<=t+r||(0<=e&&e<=6&&(0==r||6==r)||0<=r&&r<=6&&(0==e||6==e)||2<=e&&e<=4&&2<=r&&r<=4)?this.modules[a+e][t+r]=!0:this.modules[a+e][t+r]=!1},setupTimingPattern:function(){for(var a=8;a<this.moduleCount-8;a++)null==this.modules[a][6]&&(this.modules[a][6]=a%2==0),null==this.modules[6][a]&&(this.modules[6][a]=a%2==0)},setupTypeInfo:function(a,t){for(var e=s.M,r=0;r<15;r++){var n=!a&&(1&r)==0;if(r<6)this.modules[r][8]=n;else if(r<8)this.modules[r+1][8]=n;else if(r<9)this.modules[8][15-r-1]=n;else if(r<15)this.modules[this.moduleCount-15+r][8]=n}for(r=0;r<15;r++){n=!a&&(1&r)==0;var o=this.moduleCount-1-8;if(r<8)this.modules[8][r]=n;else if(r<9)this.modules[15-r-1][8]=n;else if(r<15)this.modules[8][o-(15-r-1)]=n}},mapData:function(a,t){for(var e=this.moduleCount-1,r=7,n=0,o=this.moduleCount-1;0<o;o-=2){for(6==o&&o--;0<=e;e++){for(var i=0;i<2;i++)null==this.modules[o-i][e]&&(n<a.length?(this.modules[o-i][e]=(a[n]>>>r&1)==1,n++,(0==--r&&(r=7))):this.modules[o-i][e]=!1);e+=o%4==0?1:-1}e+=o%4==0?-1:1}},createData:function(a,t){var e=function(a,t){for(var e=[],r=0;r<a.length;r++){var n=a[r];e.push(n.getLength()<<10|c.MODE_8BIT_BYTE<<12);for(var o=0;o<n.getLength();o++)e.push(n.parsedData[o])}for(var i=[],s=0;s<e.length;s++)for(var u=e[s],h=7;0<=h;h--)i.push((u>>>h&1)==1?1:0);var l=Math.ceil((4*a.length+17)/8)*8;for(;i.length%8!=0;)i.push(0);for(;i.length<l;)i.push(0);for(var f=[],d=0;d<i.length;d+=8){for(var m=0,p=0;p<8;p++)m=m<<1|i[d+p];f.push(m)}return f}(this.dataList,t);return e},getBestMaskPattern:function(){return 0}};function l(a,t){var e=document.createElement("canvas"),r=e.getContext("2d");a.make();var n=a.getModuleCount(),o=180,i=Math.floor(o/n);e.width=e.height=i*n,r.clearRect(0,0,e.width,e.height);for(var s=0;s<n;s++)for(var u=0;u<n;u++)r.fillStyle=a.isDark(u,s)?"#000":"#fff",r.fillRect(u*i,s*i,i,i);return e}window.SimpleQR={{draw:function(t){try{{var e=new i(0,s.M);e.addData(t);e.make();var a=l(e);return a}}catch(n){return null}}}}();
  </script>

  <script>
    // Valeur injectée côté serveur (string JSON sûre)
    const WIFI_TEXT = {wifiqr_json};

    // Génération du QR (lib embarquée)
    (function () {{
      const box = document.getElementById("qrbox");
      const fallback = document.getElementById("qr-fallback");
      try {{
        const canvas = window.SimpleQR?.draw(WIFI_TEXT);
        if (box && canvas) {{
          box.innerHTML = "";
          box.appendChild(canvas);
        }} else {{
          throw new Error("QR lib error");
        }}
      }} catch(e) {{
        console.error("QR error", e);
        if (fallback) {{
          fallback.classList.remove("hidden");
          fallback.textContent = "QR indisponible. Code Wi-Fi : " + WIFI_TEXT;
        }}
      }}
    }})();

    // SW pour l’installation
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('/service-worker.js');
    }}

    // Bouton installer l’app
    let deferredPrompt = null;
    const installBtn = document.getElementById('installBtn');
    window.addEventListener('beforeinstallprompt', (e) => {{
      e.preventDefault();
      deferredPrompt = e;
      if (installBtn) installBtn.style.display = 'inline-flex';
    }});
    installBtn?.addEventListener('click', async () => {{
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      installBtn.style.display = 'none';
    }});
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

    # Compose le texte du QR côté serveur + échappements
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

# ------- RUBRIQUES -------
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
