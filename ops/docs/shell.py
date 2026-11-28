import html
import json

import md

BASE = "https://fiordlandlinux.org"
GH = "https://github.com/Fiordland-Linux/fiordland"
DONATE = "https://donate.stripe.com/8x25kFfe96fn0WL6X12wU00"
DISCORD = "https://discord.gg/gy4ANH2Q9V"
MAIL = "fiordlandlinux@gmail.com"
CSS_V, JS_V, SITE_JS_V, OG_V = "38", "4", "7", "7"
TAGLINE = "A Linux distribution based on Arch, with its own installer, package manager and desktop shell."

MENUS = [
    ("Fiordland", ("/about/", "/software/", "/why/", "/low-end/", "/news/"), [
        ("/about/", "About", "What Fiordland is and who makes it"),
        ("/software/", "Software", "The parts Fiordland is made of"),
        ("/why/", "Why Fiordland", "What it does differently, compared with CachyOS and Arch"),
        ("/low-end/", "Low end PCs", "Fiordland on older hardware"),
        ("/news/", "News", "What changed in each release"),
    ]),
    ("Download", ("/download/", "/mirrors/"), [
        ("/download/", "Download the ISO", "Latest build, checksum and requirements"),
        ("/mirrors/", "Mirrors", "Servers that carry the repo and the ISOs"),
        ("/repo/x86_64/", "Package repo", "Browse the signed packages"),
    ]),
    ("Docs", ("/docs/",), [
        ("/docs/install/", "Install", "From a download to a working desktop"),
        ("/docs/first-steps/", "First steps", "What to do after the first boot"),
        ("/docs/apps/", "Installing apps", "Use tawaki for every source"),
        ("/docs/updates/", "Updates", "Stay current and know what changed"),
        ("/docs/snapshots/", "Snapshots", "Undo a bad update"),
        ("/docs/kernel/", "The kernel", "What the Fiordland kernel sets and why"),
        ("/docs/crest/", "The crest shell", "The Hyprland shell and its shortcuts"),
        ("/docs/live-wallpapers/", "Live wallpapers", "Wallpaper Engine on Fiordland"),
        ("/docs/help/", "Getting help", "Where to ask and what to include"),
    ]),
    ("Community", ("/contribute/", "/security/"), [
        ("/wiki/", "Wiki", "Community guides and fixes"),
        (DISCORD, "Discord", "Chat with users and the developer"),
        (GH, "GitHub", "Source code and issues"),
        ("/contribute/", "Contribute", "Reports, docs and code"),
        ("/security/", "Security", "Report a problem, check signatures"),
    ]),
]

DOCS_GROUPS = [
    ("Getting started", [("/docs/install/", "Install Fiordland"), ("/docs/first-steps/", "First steps")]),
    ("Using Fiordland", [("/docs/apps/", "Installing apps"), ("/docs/updates/", "Updates"), ("/docs/snapshots/", "Snapshots and rollback"),
                         ("/docs/kernel/", "The kernel"), ("/docs/crest/", "The crest shell"), ("/docs/live-wallpapers/", "Live wallpapers")]),
    ("Help", [("/docs/help/", "Getting help"), ("/wiki/", "Community wiki")]),
]
DOCS_ORDER = [h for _, links in DOCS_GROUPS for h, _ in links if h.startswith("/docs/")]
DOCS_TITLES = {h: t for _, links in DOCS_GROUPS for h, t in links}


def esc(s):
    return html.escape(s, quote=True)


def header(cur=""):
    out = []
    for label, prefixes, links in MENUS:
        on = " cur" if any(cur.startswith(p) for p in prefixes) else ""
        wide = " wide" if len(links) > 6 else ""
        rows = "".join(f'<a href="{esc(h)}"><b>{esc(t)}</b><span>{esc(d)}</span></a>' for h, t, d in links)
        out.append(f'<div class="dd{on}"><button class="mi" type="button" aria-expanded="false" aria-haspopup="true">{esc(label)}<i></i></button><div class="dd-menu{wide}">{rows}</div></div>')
    out.append('<a class="mi" href="/donate/">Donate</a>')
    return ('<a class="skip" href="#main">Skip to content</a>\n<header class="nav">\n  <div class="nav-in">\n'
            '    <a class="brand" href="/" aria-label="Fiordland Linux home"><img src="/assets/brand/lockup-dark.svg" alt="Fiordland Linux" width="152" height="32"></a>\n'
            '    <button class="burger" type="button" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>\n'
            '    <nav class="menu" aria-label="Main">\n      ' + "\n      ".join(out) + '\n    </nav>\n'
            '    <a class="btn sm" href="/download/">Download</a>\n  </div>\n</header>')


def footer():
    cols = "".join(
        f'<div><h2>{esc(label)}</h2>' + "".join(f'<a href="{esc(h)}">{esc(t)}</a>' for h, t, _ in links) + '</div>'
        for label, _, links in MENUS)
    return (f'<footer class="foot">\n  <div class="wrap foot-grid">\n    <div class="foot-brand"><a href="/"><img src="/assets/brand/lockup-dark.svg" alt="Fiordland Linux" width="152" height="32"></a>'
            f'<p>{esc(TAGLINE)}</p><a class="btn sm ghost" href="/donate/">Donate</a></div>\n    {cols}\n  </div>\n'
            '  <div class="wrap foot-badge"><span class="badge88"><button type="button" class="badge88-btn" title="Copy the HTML for this button"><img src="/assets/fiordland-88x31.gif" width="88" height="31" alt="Powered by Fiordland Linux"></button><span class="badge88-msg">Use Fiordland? Click to copy our button for your site.</span></span></div>\n'
            f'  <div class="wrap foot-bot"><span>Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.</span>'
            f'<span><a href="mailto:{MAIL}">{MAIL}</a> &middot; Created by <a href="https://apollo44.lat" rel="author">Apollo</a> (<a href="https://github.com/3cfl">3cfl</a>) &middot; <a href="https://ivy.rest">ivy.rest</a></span></div>\n</footer>')


def docs_sidebar(cur):
    g = ""
    for name, links in DOCS_GROUPS:
        li = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == cur else ""}>{esc(t)}</a></li>' for h, t in links)
        g += f'<div class="grp"><p>{esc(name)}</p><ul>{li}</ul></div>'
    return f'<aside class="dside" aria-label="Docs navigation"><input id="dq" type="search" placeholder="Filter pages" aria-label="Filter docs pages">{g}</aside>'


def pager(cur):
    if cur not in DOCS_ORDER:
        return ""
    i = DOCS_ORDER.index(cur)
    prev = f'<a class="pg prev" href="{DOCS_ORDER[i - 1]}"><span>Previous</span>{esc(DOCS_TITLES[DOCS_ORDER[i - 1]])}</a>' if i else "<span></span>"
    nxt = f'<a class="pg next" href="{DOCS_ORDER[i + 1]}"><span>Next</span>{esc(DOCS_TITLES[DOCS_ORDER[i + 1]])}</a>' if i + 1 < len(DOCS_ORDER) else "<span></span>"
    return f'<nav class="pager" aria-label="Previous and next page">{prev}{nxt}</nav>'


def crumbs(path, title):
    items = [("Home", "/")]
    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) > 1 and parts[0] == "docs":
        items.append(("Docs", "/docs/"))
    if parts:
        items.append((title, path))
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(items)]}


def head(title, desc, path, full_title=False, noindex=False, ld=None):
    title, desc = md.plain(title, False), md.plain(desc, False)
    t = title if full_title else f"{title} | Fiordland Linux"
    url = BASE + (path or "/")
    img = f"{BASE}/assets/og.png?v={OG_V}"
    alt = "Fiordland Linux logo and tagline"
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"
    graph = md.clean_ld(ld if ld is not None else [crumbs(path or "/", title)])
    lines = [
        '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(t)}</title>", f'<meta name="description" content="{esc(desc)}">', f'<meta name="robots" content="{robots}">',
        f'<link rel="canonical" href="{url}">' if not noindex else "",
        '<meta name="theme-color" content="#1c1c1c">', '<meta name="author" content="Apollo (3cfl)">', '<meta name="color-scheme" content="dark">',
        '<link rel="icon" href="/assets/brand/favicon.svg?v=2" type="image/svg+xml">', '<link rel="icon" href="/assets/brand/favicon.ico?v=2" sizes="48x48">',
        '<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">', '<link rel="manifest" href="/site.webmanifest">',
        '<meta property="og:type" content="website">', f'<meta property="og:url" content="{url}">', f'<meta property="og:title" content="{esc(t)}">',
        f'<meta property="og:description" content="{esc(desc)}">', f'<meta property="og:image" content="{img}">',
        '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">', f'<meta property="og:image:alt" content="{alt}">',
        '<meta property="og:site_name" content="Fiordland Linux">', '<meta property="og:locale" content="en_US">',
        '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{esc(t)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">', f'<meta name="twitter:image" content="{img}">', f'<meta name="twitter:image:alt" content="{alt}">',
        '<link rel="preload" href="/assets/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">',
        f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, separators=(",", ":"), ensure_ascii=False)}</script>',
    ]
    return "\n".join(x for x in lines if x)


def scripts():
    return f'<script src="/assets/js/site.js?v={SITE_JS_V}" defer></script>\n<script src="/assets/js/nav.js?v={JS_V}" defer></script>'


def document(title, desc, path, main, full_title=False, ld=None, noindex=False, cur=None):
    doc = (f'<!doctype html>\n<html lang="en">\n<head>\n{head(title, desc, path, full_title, noindex, ld)}\n</head>\n<body>\n'
           f'{header(cur if cur is not None else path)}\n{main}\n{cta()}\n{footer()}\n{scripts()}\n</body>\n</html>\n')
    return md.clean_html(doc)


def page_head(title, lede):
    return (f'<section class="page-head"><div class="wrap"><h1>{html.escape(title)}</h1><p class="lede">{lede}</p></div>'
            '<svg class="edge" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true"><path class="to-base" d="M0 52C180 92 360 94 560 62C760 30 940 8 1140 30C1260 43 1360 60 1440 52V90H0Z"/></svg></section>')


def cta():
    return ('<section class="band cta-band" aria-labelledby="questions-h">\n'
            '  <svg class="edge top" viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true"><path class="to-light" d="M0 80V52L1440 8V80Z"/></svg>\n'
            '  <div class="wrap"><h2 id="questions-h">Questions?</h2><p class="sub">Fiordland is a small project. Ask in the Discord, search the wiki or open an issue.</p>\n'
            f'  <p class="links-row"><a href="{DISCORD}">Discord</a><a href="/wiki/">Wiki</a><a href="{GH}/issues/new/choose">GitHub issues</a><a href="/contribute/">Contribute</a></p></div>\n'
            '  <svg class="edge" viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true"><path class="to-base" d="M0 80V56Q720 -16 1440 56V80Z"/></svg>\n</section>')


def plain_page(title, desc, path, lede, inner, wide=False, **kw):
    main = f'{page_head(title, lede)}\n<main id="main" class="wrap page{" wide" if wide else ""}">\n{inner}\n</main>'
    return document(title, desc, path, main, **kw)


def docs_page(title, desc, path, lede, inner, **kw):
    main = (f'<main id="main" class="wrap dlayout">\n{docs_sidebar(path)}\n<article class="dmain">\n<h1>{html.escape(title)}</h1>\n<p class="lede">{lede}</p>\n{inner}\n{pager(path)}\n</article>\n'
            '<aside class="dtoc" aria-label="On this page"><p>On this page</p><ul id="toc"></ul></aside>\n</main>')
    return document(title, desc, path, main, **kw)
