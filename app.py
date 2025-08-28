# app.py — Portail sécurisé + Guide (Flask + Tailwind + PWA)
from datetime import datetime, timezone
from flask import Flask, request, redirect, Response, session, url_for

app = Flask(__name__)

# 🔐 Clé secrète (change-la !)
app.secret_key = "change-moi-par-une-grosse-cle-secrete-aleatoire"

# ========= CONFIG =========
# Image de fond (mets ton fichier dans /static/images/bg.jpg)
BG_URL = "/static/images/bg.jpg"

# Wi-Fi (remplis avec tes infos)
WIFI_SSID = "TON_SSID"
WIFI_PASS = "TON_MDP_WIFI"
WIFI_AUTH = "WPA"  # WPA, WEP, ou nopass

# TOKENS : 1 ligne par séjour (mets large au début). 'lang' = langue choisie par défaut.
TOKENS = [
    {"token": "Marseille25", "lang": "fr",
     "start": "2020-01-01T00:00:00Z", "end": "2030-12-31T23:59:59Z"},
]

# ========= PAGES (HTML) =========
# ⚠️ On utilise .format(...). Donc on double TOUTES les accolades CSS {{ }}.

LOGIN_HTML = """<!doctype html>
<html lang="{lang}">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{t_title}</title>
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0b1736">
<link rel="apple-touch-icon" href="/icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<style>
  :root {{ --bg: url('{bg_url}'); }}
  body {{ font-family:'Poppins',system-ui,Segoe UI,Roboto,Arial,sans-serif; }}
  @keyframes fadeIn {{ from {{opacity:0}} to {{opacity:1}} }}
  @keyframes floatUp {{ from {{opacity:0; transform:translateY(12px)}} to {{opacity:1; transform:none}} }}
</style>
<body class="min-h-screen bg-cover bg-center" style="background-image:var(--bg)">
  <div class="fixed inset-0 bg-black/60 animate-[fadeIn_.6s_ease-out_forwards]"></div>

  <div class="relative mx-auto max-w-xl px-4">
    <div class="mt-24 md:mt-28 animate-[floatUp_.6s_.1s_ease-out_forwards] bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-6 md:p-8 text-center">
      <div class="flex justify-center gap-2 mb-3">
        <button class="px-3 py-1 rounded-lg border text-sm" data-lang="fr">FR</button>
        <button class="px-3 py-1 rounded-lg border text-sm" data-lang="en">EN</button>
        <button class="px-3 py-1 rounded-lg border text-sm" data-lang="it">IT</button>
        <button class="px-3 py-1 rounded-lg border text-sm" data-lang="es">ES</button>
      </div>

      <h1 class="text-2xl font-semibold flex items-center justify-center gap-2">
        <span>🔒</span> {t_title}
      </h1>
      <p class="mt-2 text-slate-600">{t_sub}</p>

      <form method="POST" class="mt-5" onsubmit="btn.disabled=true;btn.textContent='{t_connecting}'">
        <input name="token" placeholder="{t_placeholder}" required autofocus
               class="w-full rounded-xl border-2 border-slate-200 focus:border-blue-600 focus:ring-0 px-4 py-3 outline-none transition"/>
        <input type="hidden" name="ui_lang" id="ui_lang" value="{lang}">
        <div class="mt-4 flex justify-center">
          <button name="btn" id="btn" type="submit"
                  class="rounded-xl bg-blue-900 text-white px-5 py-3 font-semibold shadow hover:shadow-lg transition">
            {t_cta}
          </button>
        </div>
      </form>

      <div class="min-h-[20px] mt-2 text-center text-red-600 text-sm">{message}</div>

      <div class="mt-4">
        <button id="installBtn" class="rounded-xl bg-slate-700 text-white px-4 py-2 text-sm">{t_install}</button>
        <p id="iosHint" class="text-slate-500 text-xs mt-2 hidden">{t_ioshint}</p>
      </div>
    </div>

    <p class="text-center text-white/80 text-xs mt-4">
      Marseille · Fort Saint-Jean · Vieux-Port
    </p>
  </div>

<script>
  // Sélecteur de langue
  const dict = {dict};
  function setLang(l) {{
    const t = dict[l] || dict['fr'];
    document.documentElement.lang = l;
    document.title = t.t_title;
    document.querySelector('h1').innerHTML = "🔒 " + t.t_title;
    document.querySelector('p.text-slate-600').innerHTML = t.t_sub;
    document.querySelector('input[name=token]').placeholder = t.t_placeholder;
    document.getElementById('btn').textContent = t.t_cta;
    document.getElementById('ui_lang').value = l;
    document.getElementById('installBtn').textContent = t.t_install;
    document.getElementById('iosHint').textContent = t.t_ioshint;
    localStorage.setItem('ui_lang', l);
  }}
  document.querySelectorAll('[data-lang]').forEach(b => b.addEventListener('click', () => setLang(b.dataset.lang)));

  // Init langue : préférences → URL ?ui= → FR
  (function() {{
    const url = new URL(window.location);
    const fromUrl = url.searchParams.get('ui');
    const stored = localStorage.getItem('ui_lang');
    const def = '{lang}';
    setLang((fromUrl || stored || def).toLowerCase());
  }})();

  // PWA install
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js');
  let deferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {{
    e.preventDefault(); deferredPrompt = e;
    document.getElementById('installBtn').onclick = async () => {{
      if (!deferredPrompt) return;
      deferredPrompt.prompt(); deferredPrompt = null;
    }};
  }});
  // iOS hint
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  if (isIOS && isSafari) document.getElementById('iosHint').classList.remove('hidden');
</script>
</body>
</html>
"""

GUIDE_HTML = """<!doctype html>
<html lang="{lang}">
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{t_guide}</title>
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0b1736">
<link rel="apple-touch-icon" href="/icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<style>
  :root {{ --bg: url('{bg_url}'); }}
  body {{ font-family:'Poppins',system-ui,Segoe UI,Roboto,Arial,sans-serif; }}
  @keyframes fadeIn {{ from {{opacity:0}} to {{opacity:1}} }}
  @keyframes floatUp {{ from {{opacity:0; transform:translateY(12px)}} to {{opacity:1; transform:none}} }}
</style>
<body class="min-h-screen bg-cover bg-center" style="background-image:var(--bg)">
  <div class="fixed inset-0 bg-black/60 animate-[fadeIn_.6s_ease-out_forwards]"></div>

  <header class="relative max-w-5xl mx-auto px-4 pt-6 flex items-center justify-between text-white">
    <h1 class="text-xl md:text-2xl font-semibold">🏡 {t_guide}</h1>
    <a href="{logout_url}" class="text-white/90 hover:text-white underline">{t_logout}</a>
  </header>

  <main class="relative max-w-5xl mx-auto px-4 pb-20">
    <section class="mt-6 md:mt-10 grid md:grid-cols-2 gap-6 animate-[floatUp_.6s_.1s_ease-out_forwards]">
      <!-- Carte Wi-Fi -->
      <div class="bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-6">
        <h2 class="text-lg font-semibold">Wi-Fi</h2>
        <p class="mt-2 text-slate-700">{t_wifi_network} <b id="ssid"></b><br>{t_wifi_pass} <b id="pwd"></b></p>

        <div class="mt-4 grid md:grid-cols-2 gap-3 items-start">
          <div>
            <div id="wifi-qr" class="bg-white rounded-xl p-3 inline-block"></div>
            <p class="text-slate-500 text-xs mt-2">{t_wifi_hint}</p>
          </div>
          <div class="flex flex-col gap-2">
            <button id="copy-pass" class="rounded-xl bg-blue-900 text-white px-4 py-2 font-semibold shadow hover:shadow-lg">
              {t_copy}
            </button>
            <a id="open-wifi-settings" class="rounded-xl bg-slate-800 text-white px-4 py-2 font-semibold text-center"
               href="android.intent.action.WIFI_SETTINGS">
              {t_open_wifi}
            </a>
          </div>
        </div>
      </div>

      <!-- Carte Restaurants -->
      <div class="bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-6">
        <h2 class="text-lg font-semibold">{t_food_title}</h2>
        <div class="mt-3 grid gap-3">
          <a class="block bg-slate-100 rounded-xl p-3 hover:bg-slate-200 transition"
             target="_blank" href="https://maps.google.com/?q=Chez+Fonfon+Marseille">🍽️ Chez Fonfon</a>
          <a class="block bg-slate-100 rounded-xl p-3 hover:bg-slate-200 transition"
             target="_blank" href="https://maps.google.com/?q=La+Caravelle+Marseille">🍷 La Caravelle</a>
        </div>
      </div>

      <!-- Carte Urgences -->
      <div class="bg-white/95 backdrop-blur rounded-2xl shadow-2xl p-6 md:col-span-2">
        <h2 class="text-lg font-semibold">{t_help_title}</h2>
        <ul class="mt-3 grid md:grid-cols-3 gap-3 text-slate-700">
          <li class="bg-slate-100 rounded-xl p-3">🚑 112 (Urgences)</li>
          <li class="bg-slate-100 rounded-xl p-3">🚓 17 (Police)</li>
          <li class="bg-slate-100 rounded-xl p-3">🚒 18 (Pompiers)</li>
        </ul>
      </div>
    </section>
  </main>

<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
<script>
  // Textes traduits
  const T = {dict}[localStorage.getItem('ui_lang') || '{lang}'] || {dict}['fr'];

  // Wi-Fi
  const SSID = "{ssid}";
  const PASS = "{pwd}";
  const AUTH = "{auth}";

  document.getElementById('ssid').textContent = SSID;
  document.getElementById('pwd').textContent  = PASS;

  const WIFI_TEXT = `WIFI:T:${{AUTH}};S:${{SSID}};P:${{PASS}};;`;
  new QRCode(document.getElementById("wifi-qr"), {{
    text: WIFI_TEXT, width: 180, height: 180, correctLevel: QRCode.CorrectLevel.M
  }});

  document.getElementById('copy-pass').onclick = async () => {{
    try {{
      await navigator.clipboard.writeText(PASS);
      document.getElementById('copy-pass').textContent = T.t_copied;
      setTimeout(()=>document.getElementById('copy-pass').textContent=T.t_copy, 1500);
    }} catch (e) {{}}
  }};
</script>
</body>
</html>
"""

# Dictionnaire de traductions (UI)
I18N = {
    "fr": {
        "t_title": "Accès au guide",
        "t_sub": "Entrez <b>le mot de passe</b> fourni par votre hôte.",
        "t_placeholder": "Ex. TESTFR",
        "t_cta": "Continuer",
        "t_connecting": "Connexion…",
        "t_install": "Installer l’app",
        "t_ioshint": "Sur iPhone : Partager → « Ajouter à l’écran d’accueil »",
        "t_guide": "Guide de l’appartement",
        "t_logout": "Se déconnecter",
        "t_wifi_network": "Réseau :",
        "t_wifi_pass": "Mot de passe :",
        "t_wifi_hint": "Scannez ce QR avec l’appareil photo pour vous connecter.",
        "t_copy": "Copier le mot de passe",
        "t_copied": "Copié ✅",
        "t_open_wifi": "Ouvrir les réglages Wi-Fi (Android)",
        "t_food_title": "Bons plans resto",
        "t_help_title": "Urgences & contacts",
    },
    "en": {
        "t_title": "Guide Access",
        "t_sub": "Enter the <b>password</b> provided by your host.",
        "t_placeholder": "e.g. TESTEN",
        "t_cta": "Continue",
        "t_connecting": "Connecting…",
        "t_install": "Install app",
        "t_ioshint": "On iPhone: Share → “Add to Home Screen”",
        "t_guide": "Apartment Guide",
        "t_logout": "Log out",
        "t_wifi_network": "Network:",
        "t_wifi_pass": "Password:",
        "t_wifi_hint": "Scan this QR with the camera to connect.",
        "t_copy": "Copy password",
        "t_copied": "Copied ✅",
        "t_open_wifi": "Open Wi-Fi settings (Android)",
        "t_food_title": "Food & restaurants",
        "t_help_title": "Emergencies & contacts",
    },
    "it": {
        "t_title": "Accesso alla guida",
        "t_sub": "Inserisci la <b>password</b> fornita dal tuo host.",
        "t_placeholder": "es. TESTIT",
        "t_cta": "Continua",
        "t_connecting": "Connessione…",
        "t_install": "Installa app",
        "t_ioshint": "Su iPhone: Condividi → “Aggiungi a Home”",
        "t_guide": "Guida dell’appartamento",
        "t_logout": "Esci",
        "t_wifi_network": "Rete:",
        "t_wifi_pass": "Password:",
        "t_wifi_hint": "Scansiona questo QR con la fotocamera per connetterti.",
        "t_copy": "Copia password",
        "t_copied": "Copiato ✅",
        "t_open_wifi": "Apri impostazioni Wi-Fi (Android)",
        "t_food_title": "Ristoranti consigliati",
        "t_help_title": "Emergenze & contatti",
    },
    "es": {
        "t_title": "Acceso a la guía",
        "t_sub": "Introduce la <b>contraseña</b> proporcionada por tu anfitrión.",
        "t_placeholder": "p. ej. TESTES",
        "t_cta": "Continuar",
        "t_connecting": "Conectando…",
        "t_install": "Instalar app",
        "t_ioshint": "En iPhone: Compartir → “Añadir a pantalla de inicio”",
        "t_guide": "Guía del apartamento",
        "t_logout": "Cerrar sesión",
        "t_wifi_network": "Red:",
        "t_wifi_pass": "Contraseña:",
        "t_wifi_hint": "Escanee este QR con la cámara para conectarse.",
        "t_copy": "Copiar contraseña",
        "t_copied": "Copiado ✅",
        "t_open_wifi": "Abrir ajustes Wi-Fi (Android)",
        "t_food_title": "Restaurantes",
        "t_help_title": "Emergencias y contactos",
    },
}

# ========= LOGIQUE UTILITAIRE =========
def _now_utc():
    return datetime.now(timezone.utc)

def _parse_iso(iso_str: str):
    try:
        return datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def _token_valid(token: str):
    now = _now_utc()
    for t in TOKENS:
        if t.get("token") == token:
            start = _parse_iso(t.get("start", "1970-01-01T00:00:00Z"))
            end   = _parse_iso(t.get("end",   "2999-12-31T23:59:59Z"))
            if start <= now <= end:
                return t
    return None

def _html(s: str) -> Response:
    return Response(s, mimetype="text/html; charset=utf-8")

# ========= ROUTES =========
@app.get("/")
def login_get():
    # langue par défaut (FR) ou stockée
    lang = (request.args.get("ui") or session.get("ui_lang") or "fr").lower()
    t = I18N.get(lang, I18N["fr"])
    html = LOGIN_HTML.format(
        lang=lang, bg_url=BG_URL, dict=I18N,
        t_title=t["t_title"], t_sub=t["t_sub"],
        t_placeholder=t["t_placeholder"], t_cta=t["t_cta"],
        t_connecting=t["t_connecting"], t_install=t["t_install"], t_ioshint=t["t_ioshint"],
        message=""
    )
    return _html(html)

@app.post("/")
def login_post():
    token = (request.form.get("token") or "").strip()
    ui_lang = (request.form.get("ui_lang") or "fr").lower()
    match = _token_valid(token)
    if match:
        session["ok"] = True
        session["token"] = token
        session["ui_lang"] = ui_lang or match.get("lang", "fr")
        return redirect(url_for("guide"))
    # erreur
    t = I18N.get(ui_lang, I18N["fr"])
    html = LOGIN_HTML.format(
        lang=ui_lang, bg_url=BG_URL, dict=I18N,
        t_title=t["t_title"], t_sub=t["t_sub"],
        t_placeholder=t["t_placeholder"], t_cta=t["t_cta"],
        t_connecting=t["t_connecting"], t_install=t["t_install"], t_ioshint=t["t_ioshint"],
        message="Code invalide ou expiré."
    )
    return _html(html)

@app.get("/guide")
def guide():
    if not session.get("ok"):
        return redirect(url_for("login_get"))
    lang = (session.get("ui_lang") or "fr").lower()
    t = I18N.get(lang, I18N["fr"])
    html = GUIDE_HTML.format(
        lang=lang, bg_url=BG_URL, dict=I18N,
        t_guide=t["t_guide"], t_logout=t["t_logout"],
        t_wifi_network=t["t_wifi_network"], t_wifi_pass=t["t_wifi_pass"],
        t_wifi_hint=t["t_wifi_hint"], t_copy=t["t_copy"], t_copied=t["t_copied"],
        t_open_wifi=t["t_open_wifi"], t_food_title=t["t_food_title"], t_help_title=t["t_help_title"],
        logout_url=url_for('logout'),
        ssid=WIFI_SSID, pwd=WIFI_PASS, auth=WIFI_AUTH
    )
    return _html(html)

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_get"))

# PWA manifest & service worker minimal
@app.get("/manifest.webmanifest")
def manifest():
    return Response("""{
  "name": "Guide de l'appartement",
  "short_name": "Guide",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0b1736",
  "theme_color": "#0b1736",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}""", mimetype="application/manifest+json")

@app.get("/service-worker.js")
def sw():
    return Response("""self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => { self.clients.claim(); });
self.addEventListener('fetch', e => { /* pass-through */ });""",
    mimetype="text/javascript")
