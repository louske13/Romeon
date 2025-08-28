HTML = """<!doctype html>
<html lang="fr">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Accès guide</title>
<!-- Police élégante -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
  /* IMPORTANT: évite que l’input déborde */
  *, *::before, *::after{{ box-sizing:border-box; }}

  body{{ 
    font-family:'Poppins',system-ui,Segoe UI,Roboto,Arial,sans-serif;
    background: url("https://png.pngtree.com/thumb_back/fh260/background/20230323/pngtree-marseille-old-port-and-fort-saint-jean-and-museum-of-european-photo-image_2100164.jpg") no-repeat center center fixed;
    background-size: cover;
    margin: 0;
  }}
  /* overlay plus marqué pour améliorer le contraste */
  .overlay{{ position:fixed; inset:0; background:rgba(0,0,0,.55); }}

  .wrap{{ 
    position:relative;
    width:min(520px, calc(100% - 32px));
    margin:10vh auto;
    background:rgba(255,255,255,0.94);
    padding:24px;
    border-radius:16px;
    box-shadow:0 14px 40px rgba(0,0,0,.18);
  }}

  h1{{ font-size:22px; margin:0 0 8px; display:flex; align-items:center; gap:8px; }}
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
  }}
  input:focus{{ border-color:#0078ff; box-shadow:0 0 0 3px rgba(0,120,255,.12); }}

  .actions{{ margin-top:12px; display:flex; justify-content:flex-start; }}
  button[type=submit]{{ 
    background:#004080; 
    color:#fff; 
    border:0; 
    padding:12px 18px; 
    border-radius:12px; 
    font-weight:600; 
    cursor:pointer; 
    transition:transform .04s ease, opacity .15s ease;
  }}
  button[type=submit]:hover{{ opacity:.95; }}
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
