from datetime import datetime
from html import escape
from pathlib import Path

import yfinance as yf

# La page est générée à côté de ce script : analytics/1/news.html
OUT = Path(__file__).parent / "news.html"

TICKERS = [
"AAPL", "ASML.AS", "LLY", "NVDA", "MU", "RR.L", "CNQ.TO",
 "MA", "LRCX", "XOM", "GOOGL", "6857.T", "V", "BHP.AX", "KLAC",
 "AMAT", "ITX.MC", "CSCO", "ALV.DE", "COST", "TJX", "VRTX", "CRWD",
 "CAT", "IBE.MC"
]
NEWS_PER_TICKER = 5
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
        "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def lire_article(n):
    """Accepte l'ancien et le nouveau format renvoyés par yfinance."""
    c = n.get("content") or {}
    titre = n.get("title") or c.get("title") or ""
    lien = (n.get("link")
            or (c.get("canonicalUrl") or {}).get("url")
            or (c.get("clickThroughUrl") or {}).get("url") or "")
    source = n.get("publisher") or (c.get("provider") or {}).get("displayName") or ""
    date = None
    if n.get("providerPublishTime"):
        date = datetime.fromtimestamp(n["providerPublishTime"])
    elif c.get("pubDate"):
        try:
            date = datetime.fromisoformat(c["pubDate"].replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass
    return titre, lien, source, date


def collecter():
    articles = {}                       # lien -> article (évite les doublons)
    for t in TICKERS:
        try:
            news = yf.Search(t, news_count=NEWS_PER_TICKER).news[:NEWS_PER_TICKER]
        except Exception as e:
            print(f"[{t}] erreur : {e}")
            continue
        for n in news:
            titre, lien, source, date = lire_article(n)
            if not titre or not lien:
                continue
            a = articles.setdefault(lien, dict(titre=titre, source=source, date=date, tickers=[]))
            if t not in a["tickers"]:
                a["tickers"].append(t)
    return sorted(articles.items(), key=lambda kv: kv[1]["date"] or datetime.min, reverse=True)


def fmt_date(d):
    return f"{d.day} {MOIS[d.month - 1]} {d.year}" if d else ""


TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Velocity – Actualités | Winners Portfolio Management</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../css/reset.css">
  <link rel="stylesheet" href="../../css/news.css">
</head>
<body class="news-page theme-velocity">

  <header class="topbar">
    <a class="brand" href="../../index.html">
      <img src="../../img/logo.png" alt="">
      <span>Winners Portfolio Management</span>
    </a>
    <nav class="pager" aria-label="Analyses Velocity">
      <span class="label">Velocity · Analyse</span>
      <a href="1.html">1</a><a href="2.html">2</a><a href="3.html">3</a>
      <a href="4.html">4</a><a href="5.html">5</a><a href="6.html">6</a>
    </nav>
    <nav class="actions">
      <a href="../../2.html">← Tableau de bord</a>
      <a href="../../index.html">Accueil</a>
    </nav>
  </header>

  <main>
    <div class="page-head">
      <span class="tag">Velocity · Actualités</span>
      <h1>L'actualité des 25 actifs</h1>
      <p class="lead">Les derniers articles publiés sur les entreprises du portefeuille. __COUNT__ articles, mis à jour le __DATE__.</p>
    </div>

    <div class="chips" id="chips">__CHIPS__</div>
    <div class="grid" id="grid">__CARDS__</div>
    <p class="empty" id="empty" hidden>Aucun article pour ce filtre.</p>
  </main>

  <footer>
    <p>Source : Yahoo Finance. Les liens s'ouvrent sur des sites externes. Projet pédagogique : ne constitue pas un conseil en investissement.</p>
  </footer>

  <script>
    const chips = document.querySelectorAll('.chip');
    const cards = document.querySelectorAll('.card');
    const empty = document.getElementById('empty');
    chips.forEach(chip => chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.toggle('active', c === chip));
      const t = chip.dataset.t;
      let n = 0;
      cards.forEach(card => {
        const ok = t === 'all' || card.dataset.tickers.split(' ').includes(t);
        card.hidden = !ok;
        if (ok) n++;
      });
      empty.hidden = n > 0;
    }));
  </script>
</body>
</html>
"""


def construire(articles):
    presents = [t for t in TICKERS if any(t in a["tickers"] for _, a in articles)]
    chips = '<button class="chip active" data-t="all">Tous</button>' + "".join(
        f'<button class="chip" data-t="{escape(t)}">{escape(t)}</button>' for t in presents)

    cartes = []
    for lien, a in articles:
        tk = a["tickers"]
        tags = "".join(f'<span class="tag-t">{escape(t)}</span>' for t in tk[:4])
        if len(tk) > 4:
            tags += f'<span class="tag-t">+{len(tk) - 4}</span>'
        meta = " · ".join(x for x in (a["source"], fmt_date(a["date"])) if x)
        cartes.append(
            f'<article class="card" data-tickers="{escape(" ".join(tk))}">'
            f'<div class="meta">{escape(meta)}</div>'
            f'<h3>{escape(a["titre"])}</h3>'
            f'<div class="tags">{tags}</div>'
            f'<a class="read" href="{escape(lien, quote=True)}" target="_blank" rel="noopener">Lire l\'article →</a>'
            f'</article>')

    return (TEMPLATE
            .replace("__COUNT__", str(len(articles)))
            .replace("__DATE__", fmt_date(datetime.now()))
            .replace("__CHIPS__", chips)
            .replace("__CARDS__", "\n".join(cartes)))


if __name__ == "__main__":
    articles = collecter()
    if not articles:
        print("Aucun article récupéré : news.html n'a pas été modifié.")
    else:
        OUT.write_text(construire(articles), encoding="utf-8")
        print(f"{len(articles)} articles écrits dans {OUT}")