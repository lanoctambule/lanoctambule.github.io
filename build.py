#!/usr/bin/env python3
"""Générateur de blog statique.

Lit les articles du dossier `posts/`, les pages du dossier `pages/` et le
fichier `config.json`, puis produit le site complet dans le dossier `public/`.
Seule dépendance : la bibliothèque `markdown` (pip install markdown).

Aucun script externe, aucune police externe, aucun cookie : le site généré
n'effectue aucune requête vers un service tiers.
"""

import html
import json
import math
import os
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
AFFILIATE = []  # rempli depuis config.json (« affiliate_markers »)

MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
          "août", "septembre", "octobre", "novembre", "décembre"]


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------

def fail(message):
    print(f"\n[ERREUR] {message}\n", file=sys.stderr)
    sys.exit(1)


def fr_date(d):
    jour = "1er" if d.day == 1 else str(d.day)
    return f"{jour} {MONTHS[d.month - 1]} {d.year}"


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text or "sans-titre"


def esc(text):
    return html.escape(str(text), quote=True)


def parse_front_matter(text, source):
    """Sépare l'en-tête (entre deux lignes '---') du corps de l'article."""
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        fail(f"Le fichier « {source} » doit commencer par un en-tête entre deux lignes '---'.")
    parts = text.split("---", 2)
    if len(parts) < 3:
        fail(f"L'en-tête du fichier « {source} » n'est pas fermé par une seconde ligne '---'.")
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def french_typography(fragment):
    """Insère les espaces insécables de la typographie française
    (avant : ; ! ? » et après «), hors balises, code et blocs préformatés."""
    pieces = re.split(r"(<[^>]+>)", fragment)
    protected = 0
    for i, piece in enumerate(pieces):
        if piece.startswith("<"):
            tag = piece.lower()
            if re.match(r"<(pre|code|script|style)[\s>]", tag):
                protected += 1
            elif re.match(r"</(pre|code|script|style)>", tag):
                protected = max(0, protected - 1)
            continue
        if protected:
            continue
        piece = re.sub(r"[ \u00a0]+([;!?])", "\u202f\\1", piece)
        piece = re.sub(r"[ \u00a0]+([:»])", "\u00a0\\1", piece)
        piece = re.sub(r"(«)[ \u00a0]+", "\\1\u00a0", piece)
        pieces[i] = piece
    return "".join(pieces)


def mark_affiliate_links(out):
    """Signale automatiquement les liens affiliés (mention visible + rel="sponsored")."""
    if not AFFILIATE:
        return out

    def repl(m):
        href = m.group(1)
        if any(marker in href for marker in AFFILIATE):
            return (f'<a href="{href}"{m.group(2)} class="affilie" '
                    f'rel="sponsored nofollow noopener noreferrer" target="_blank">')
        return m.group(0)

    return re.sub(r'<a href="(https?://[^"]+)"([^>]*)>', repl, out)


def render_markdown(text, base, line_breaks=False):
    md = markdown.Markdown(
        extensions=["extra", "smarty", "sane_lists"] + (["nl2br"] if line_breaks else []),
        extension_configs={"smarty": {"smart_quotes": False}},
    )
    out = md.convert(text)
    # Les liens et images écrits « /images/x.jpg » tiennent compte du sous-dossier du site.
    out = re.sub(r'(href|src)="/(?!/)', rf'\1="{base}/', out)
    out = out.replace("<img ", '<img loading="lazy" ')
    out = mark_affiliate_links(out)
    return french_typography(out)


# --------------------------------------------------------------------------
# Chargement
# --------------------------------------------------------------------------

def load_config():
    path = ROOT / "config.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Le fichier config.json contient une erreur (ligne {e.lineno}) : {e.msg}. "
             "Vérifie qu'il ne manque pas un guillemet ou une virgule.")
    if os.environ.get("SITE_URL"):
        cfg["site_url"] = os.environ["SITE_URL"]
    cfg["site_url"] = cfg.get("site_url", "").rstrip("/")
    base = os.environ.get("BASE_PATH")
    if base is None:
        base = ""
    base = "/" + base.strip("/") if base.strip("/") else ""
    cfg["base"] = base
    return cfg


def load_posts(cfg):
    categories = {c["name"]: c for c in cfg["categories"]}
    posts = []
    for f in sorted((ROOT / "posts").glob("*.md")):
        if f.name.startswith("_"):
            continue
        meta, body = parse_front_matter(f.read_text(encoding="utf-8"), f.name)
        if meta.get("brouillon", meta.get("draft", "")).lower() in ("oui", "true", "1"):
            continue
        kind = meta.get("type", meta.get("format", "chronique")).lower()
        is_note = kind in ("note", "fil", "court")
        for required in (("date", "category") if is_note else ("title", "date", "category")):
            if required not in meta:
                fail(f"Il manque « {required}: » dans l'en-tête de {f.name}.")
        try:
            d = datetime.strptime(meta["date"], "%Y-%m-%d").date()
        except ValueError:
            fail(f"La date de {f.name} doit s'écrire AAAA-MM-JJ (ex. 2026-11-11).")
        if meta["category"] not in categories:
            valid = ", ".join(categories)
            fail(f"La catégorie « {meta['category']} » de {f.name} n'existe pas. "
                 f"Catégories possibles : {valid}.")
        title = meta.get("title", "")
        if title:
            stem = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", f.stem)
            slug = slugify(meta.get("slug", stem or title))
        else:
            # Une note sans titre garde la date dans son adresse, pour rester unique.
            slug = slugify(meta.get("slug", f.stem))
        words = len(re.findall(r"\w+", body))
        plain = re.sub(r"[#*_>`\[\]!]|\(([^)]*)\)", "", body)
        plain = re.sub(r"\s+", " ", plain).strip()
        short = plain if len(plain) <= 70 else plain[:70].rsplit(" ", 1)[0] + "…"
        posts.append({
            "title": title,
            "display_title": title or short or f"Note du {fr_date(d)}",
            "is_note": is_note,
            "date": d,
            "category": categories[meta["category"]],
            "summary": meta.get("summary", ""),
            "image": meta.get("image", ""),
            "image_alt": meta.get("image_alt", ""),
            "slug": slug,
            "body_md": body,
            "minutes": max(1, math.ceil(words / 220)),
        })
    slugs = [p["slug"] for p in posts]
    if len(slugs) != len(set(slugs)):
        fail("Deux articles ont le même nom de fichier / identifiant (slug).")
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def load_pages(cfg):
    values = {k: v for k, v in cfg.items() if isinstance(v, str)}
    values["updated"] = fr_date(date.today())
    pages = []
    for f in sorted((ROOT / "pages").glob("*.md")):
        meta, body = parse_front_matter(f.read_text(encoding="utf-8"), f.name)
        for key, val in values.items():
            body = body.replace("{{" + key + "}}", val)
        pages.append({
            "title": meta.get("title", f.stem),
            "slug": slugify(f.stem),
            "summary": meta.get("summary", ""),
            "body_md": body,
            "nav": meta.get("menu", "").lower() in ("oui", "true", "1"),
        })
    return pages


# --------------------------------------------------------------------------
# Gabarits HTML
# --------------------------------------------------------------------------

def make_site(cfg, posts, pages):
    base = cfg["base"]
    site_title = cfg["title"]

    def u(path):
        return base + path

    def absolute(path):
        return cfg["site_url"] + path if cfg["site_url"] else None

    cat_slugs = {c["slug"] for c in cfg["categories"]}

    def layout(title, description, body, path, *, home=False, active="", kind="website", noindex=False, cat=""):
        full_title = site_title if home else f"{title} · {site_title}"
        robots_tag = '<meta name="robots" content="noindex, nofollow">' if noindex else ""
        theme_color = cfg.get("theme_color", "#171210")
        body_class = f' class="cat-{cat}"' if cat in cat_slugs else ""
        canonical = absolute(path)
        nav_items = [("/", "Accueil", "home")]
        for c in cfg["categories"]:
            nav_items.append((f"/categorie/{c['slug']}/", c["name"], c["slug"]))
        for p in pages:
            if p["nav"]:
                nav_items.append((f"/{p['slug']}/", p["title"], p["slug"]))
        nav_parts = []
        for href, label, key in nav_items:
            current = ' aria-current="page"' if key == active else ""
            cls = f' class="cat-{key}"' if key in cat_slugs else ""
            nav_parts.append(f'<li><a href="{u(href)}"{cls}{current}>{esc(label)}</a></li>')
        nav = "".join(nav_parts)
        title_tag = (f'<p class="site-title"><a href="{u("/")}">{esc(site_title)}</a></p>'
                     if not home else
                     f'<p class="site-title"><a href="{u("/")}" aria-current="page">{esc(site_title)}</a></p>')
        instagram = ""
        if cfg.get("instagram"):
            handle = cfg["instagram"].lstrip("@")
            instagram = (f' · <a href="https://www.instagram.com/{esc(handle)}/" '
                         f'rel="noopener noreferrer">Instagram</a>')
        aff_notice = (f'<p class="small">{esc(cfg["affiliation_notice"])}</p>'
                      if cfg.get("affiliation_notice") else "")
        canonical_tag = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
        rss_tag = ""
        rss_link = ""
        if cfg["site_url"]:
            rss_tag = (f'<link rel="alternate" type="application/rss+xml" title="{esc(site_title)}" '
                       f'href="{u("/rss.xml")}">')
            rss_link = f' · <a href="{u("/rss.xml")}">Flux RSS</a>'

        og_url = f'<meta property="og:url" content="{esc(canonical)}">' if canonical else ""
        return f"""<!doctype html>
<html lang="{esc(cfg['language'])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description or cfg['description'])}">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="{theme_color}">
{robots_tag}
<meta property="og:type" content="{kind}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description or cfg['description'])}">
<meta property="og:locale" content="fr_FR">
{og_url}
{canonical_tag}
{rss_tag}
<link rel="icon" href="{u('/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{u('/style.css')}">
<script src="{u('/partage.js')}" defer></script>
</head>
<body{body_class}>
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="site-header">
  {title_tag}
  <p class="orn" aria-hidden="true">❦</p>
  <nav aria-label="Navigation principale"><ul>{nav}</ul></nav>
</header>
<main id="contenu">
{body}
</main>
<footer class="site-footer">
  <p class="orn" aria-hidden="true">❦</p>
  <p>© {date.today().year} {esc(site_title)} · <a href="{u('/mentions-legales/')}">Mentions légales</a> · <a href="{u('/confidentialite/')}">Confidentialité</a>{rss_link}{instagram}</p>
  <p class="small">Ce site n'utilise ni cookies, ni outil de mesure d'audience, ni service tiers.</p>
  {aff_notice}
</footer>
</body>
</html>
"""

    def figure(p):
        if not p["image"]:
            return ""
        src = u(p["image"]) if p["image"].startswith("/") else p["image"]
        return (f'<figure class="photo"><img src="{esc(src)}" alt="{esc(p["image_alt"])}" '
                f'loading="lazy"></figure>')

    def actions(p):
        link = u("/articles/" + p["slug"] + "/")
        share_title = f'{p["display_title"]} · {site_title}'
        react = ""
        if cfg.get("instagram"):
            handle = cfg["instagram"].lstrip("@")
            react = (f'<a class="react" href="https://www.instagram.com/{esc(handle)}/" '
                     f'rel="noopener noreferrer">Réagir sur Instagram</a>')
        return (f'<div class="actions"><button type="button" class="share" hidden '
                f'data-url="{esc(link)}" data-title="{esc(share_title)}">Partager</button>'
                f'{react}<span class="share-status" role="status" aria-live="polite"></span></div>')

    def post_card(p):
        c = p["category"]
        link = u("/articles/" + p["slug"] + "/")
        chip = f'<a class="chip cat-{c["slug"]}" href="{u("/categorie/" + c["slug"] + "/")}">{esc(c["name"])}</a>'
        when = (f'<a class="when" href="{link}"><time datetime="{p["date"].isoformat()}">'
                f'{fr_date(p["date"])}</time></a>')
        if p["is_note"]:
            text = render_markdown(p["body_md"], base, line_breaks=True)
            body = f'<div class="note-text">{text}</div>' if p["body_md"] else ""
            return f"""<article class="card note cat-{c['slug']}">
  {figure(p)}
  <div class="card-body">
    <p class="meta">{chip} {when}</p>
    {body}
    {actions(p)}
  </div>
</article>"""
        summary = f'<p class="summary">{esc(p["summary"])}</p>' if p["summary"] else ""
        return f"""<article class="card chronique cat-{c['slug']}">
  {figure(p)}
  <div class="card-body">
    <p class="meta">{chip} {when} <span>{p['minutes']} min de lecture</span></p>
    <h3><a href="{link}">{esc(p['title'])}</a></h3>
    {summary}
    <p class="more"><a href="{link}">Lire la chronique →</a></p>
    {actions(p)}
  </div>
</article>"""

    outputs = {}

    # Accueil
    cards = "\n".join(post_card(p) for p in posts) or \
        '<p class="empty">Rien pour le moment. Les premières publications arrivent bientôt.</p>'
    subtagline = (f'<p class="subtagline">{esc(cfg["subtagline"])}</p>'
                  if cfg.get("subtagline") else "")
    home_body = f"""<section class="hero">
  <h1>{esc(site_title)}</h1>
  <p class="tagline">{esc(cfg['tagline'])}</p>
  {subtagline}
</section>
<section class="list">
  <h2 class="section-title">Le fil</h2>
  {cards}
</section>"""
    outputs["/"] = layout(site_title, cfg["description"], home_body, "/", home=True, active="home")

    # Articles
    for i, p in enumerate(posts):
        c = p["category"]
        rendered = render_markdown(p["body_md"], base, line_breaks=p["is_note"])
        aff_note = ""
        if 'class="affilie"' in rendered:
            note = cfg.get("affiliation_article_note",
                           "Cet article contient des liens affiliés, signalés par la mention « lien affilié ».")
            aff_note = f'<p class="aff-note">{esc(note)}</p>\n  '
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        pager = ""
        if newer or older:
            left = (f'<a href="{u("/articles/" + older["slug"] + "/")}">← {esc(older["display_title"])}</a>'
                    if older else "<span></span>")
            right = (f'<a href="{u("/articles/" + newer["slug"] + "/")}">{esc(newer["display_title"])} →</a>'
                     if newer else "<span></span>")
            pager = f'<nav class="pager" aria-label="Autres publications">{left}{right}</nav>'
        reading = "" if p["is_note"] else f" <span>{p['minutes']} min de lecture</span>"
        heading = (f'<h1 class="sr-only">{esc(p["display_title"])}</h1>' if p["is_note"]
                   else f'<h1>{esc(p["title"])}</h1>')
        body = f"""<article class="post{' post-note' if p['is_note'] else ''}">
  <header class="post-head">
    <p class="meta"><a class="chip cat-{c['slug']}" href="{u('/categorie/' + c['slug'] + '/')}">{esc(c['name'])}</a>
    <time datetime="{p['date'].isoformat()}">{fr_date(p['date'])}</time>{reading}</p>
    {heading}
  </header>
  {figure(p)}
  {aff_note}<div class="prose">
{rendered}
  </div>
  {actions(p)}
</article>
{pager}"""
        path = f"/articles/{p['slug']}/"
        outputs[path] = layout(p["display_title"], p["summary"], body, path, active=c["slug"], kind="article", cat=c["slug"])

    # Catégories
    for c in cfg["categories"]:
        subset = [p for p in posts if p["category"]["slug"] == c["slug"]]
        cards = "\n".join(post_card(p) for p in subset) or \
            '<p class="empty">Rien ici pour le moment.</p>'
        body = f"""<section class="hero small">
  <h1>{esc(c['name'])}</h1>
  <p class="tagline">{esc(c.get('description', ''))}</p>
</section>
<section class="list">
{cards}
</section>"""
        path = f"/categorie/{c['slug']}/"
        outputs[path] = layout(c["name"], c.get("description", ""), body, path, active=c["slug"], cat=c["slug"])

    # Pages (à propos, mentions légales, confidentialité…)
    for pg in pages:
        body = f"""<article class="post">
  <header class="post-head"><h1>{esc(pg['title'])}</h1></header>
  <div class="prose">
{render_markdown(pg['body_md'], base)}
  </div>
</article>"""
        path = f"/{pg['slug']}/"
        outputs[path] = layout(pg["title"], pg["summary"], body, path, active=pg["slug"])

    return outputs, u, absolute, layout


def admin_page(cfg, layout):
    """Page « Écrire » (réservée à l'éditrice) : formulaire de publication."""
    tpl = (ROOT / "templates" / "ecrire.html").read_text(encoding="utf-8")
    conf = json.dumps({
        "repo": cfg.get("github_repo", ""),
        "branch": cfg.get("github_branch", "main"),
        "categories": [c["name"] for c in cfg["categories"]],
        "blog": cfg["title"],
        "bg": cfg.get("theme_color", "#171210"),
        "site": cfg["base"] + "/",
    }, ensure_ascii=False).replace("</", "<\\/")
    body = tpl.replace("__CONFIG__", conf)
    return layout("Écrire", "", body, "/ecrire/", noindex=True)


def write_file(relative, content):
    target = OUT / relative.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main():
    global AFFILIATE
    cfg = load_config()
    AFFILIATE = list(cfg.get("affiliate_markers", []))
    posts = load_posts(cfg)
    pages = load_pages(cfg)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    static = ROOT / "static"
    if static.exists():
        shutil.copytree(static, OUT, dirs_exist_ok=True)

    outputs, u, absolute, layout = make_site(cfg, posts, pages)
    for path, content in outputs.items():
        write_file(path + "index.html", content)

    # Page « Écrire » (non référencée : absente du menu, du plan du site et des moteurs de recherche)
    write_file("/ecrire/index.html", admin_page(cfg, layout))

    # Page 404
    body_404 = f"""<section class="hero small">
  <h1>Page introuvable</h1>
  <p class="tagline">Cette page a sans doute été déplacée, ou n'a jamais existé.</p>
  <p><a href="{u('/')}">Retour à l'accueil</a></p>
</section>"""
    write_file("/404.html", layout("Page introuvable", "", body_404, "/404.html"))

    # Flux RSS, plan du site et robots.txt (si l'adresse du site est connue)
    site_url = cfg["site_url"]
    if site_url:
        now = format_datetime(datetime.now(timezone.utc))
        items = []
        for p in posts:
            link = absolute(f"/articles/{p['slug']}/")
            pub = format_datetime(datetime(p["date"].year, p["date"].month, p["date"].day,
                                           8, 0, tzinfo=timezone.utc))
            items.append(f"""<item>
<title>{esc(p['display_title'])}</title>
<link>{esc(link)}</link>
<guid>{esc(link)}</guid>
<pubDate>{pub}</pubDate>
<category>{esc(p['category']['name'])}</category>
<description>{esc(p['summary'])}</description>
</item>""")
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{esc(cfg['title'])}</title>
<link>{esc(absolute('/'))}</link>
<description>{esc(cfg['description'])}</description>
<language>{esc(cfg['language'])}</language>
<lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel></rss>
"""
        write_file("/rss.xml", rss)
        urls = "\n".join(f"<url><loc>{esc(absolute(p))}</loc></url>" for p in outputs)
        write_file("/sitemap.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
""")
        write_file("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {absolute('/sitemap.xml')}\n")
    else:
        print("Info : « site_url » est vide dans config.json, le flux RSS et le plan du site "
              "ne sont pas générés (ils le seront automatiquement une fois le site en ligne).")

    print(f"OK : {len(posts)} article(s), {len(pages)} page(s) → dossier « public/ »")


if __name__ == "__main__":
    main()
