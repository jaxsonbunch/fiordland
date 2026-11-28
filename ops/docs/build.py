"""Generate the Fiordland website.

    python3 ops/docs/build.py OUT_DIR

Every page is built from files in this repository: the guides in docs/, CONTRIBUTING.md and
SECURITY.md (rendered from Markdown), the package build files, the release notes in web/news/
and the page text in pages.py and content/. Nothing is read back from OUT_DIR except the ISO
version that ops/site/release-iso writes into the home page, and the sitemap dates.
"""
import datetime
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md
import pages
import shell
from shell import BASE, DISCORD, GH

OUT = Path(sys.argv[1])
REPO = pages.REPO
TODAY = datetime.date.today().isoformat()
DEFAULT_ISO_VERSION = "2026.11.26 build 3"

OUT.mkdir(parents=True, exist_ok=True)
NEWS = OUT / "news" if any((OUT / "news").glob("*.txt")) else REPO / "web" / "news"

sitemap = OUT / "sitemap.xml"
previous = dict(re.findall(r"<loc>" + re.escape(BASE) + r"([^<]*)</loc><lastmod>([^<]*)</lastmod>", sitemap.read_text(encoding="utf-8"))) if sitemap.exists() else {}
modified = {}


def emit(url, text):
    """Write a page, and remember when it last changed for the sitemap."""
    f = OUT / ("index.html" if url == "/" else url.strip("/") + "/index.html")
    f.parent.mkdir(parents=True, exist_ok=True)
    unchanged = f.exists() and f.read_text(encoding="utf-8") == text
    if not unchanged:
        f.write_text(text, encoding="utf-8")
    modified[url] = previous.get(url, TODAY) if unchanged else TODAY


def fragment(name):
    """Page text kept as HTML in content/, with the markup of the old site tidied. Returns (lede, body)."""
    text = (pages.CONTENT / f"{name}.html").read_text(encoding="utf-8")
    text = re.sub(r'\s*<p class="eyebrow">.*?</p>', "", text)
    for old, new in (('class="msec"', 'class="sec"'), ('<h2 class="h3">', "<h2>"), ('class="card plain"', 'class="plainbox"')):
        text = text.replace(old, new)
    lede = re.search(r'<p class="lede">(.*?)</p>', text, re.S)
    text = re.sub(r'\s*<h1[^>]*>.*?</h1>|\s*<p class="lede">.*?</p>', "", text, count=2, flags=re.S)
    return (lede.group(1) if lede else ""), text


def release_notes():
    """Newest first: (version, title, date, lines). Notes are web/news/VERSION.txt, dates come from dates.json."""
    dates_file = NEWS / "dates.json"
    dates = json.loads(dates_file.read_text(encoding="utf-8")) if dates_file.exists() else {}
    notes = sorted((p for p in NEWS.glob("*.txt") if re.fullmatch(r"\d+(\.\d+){1,3}", p.stem)), key=lambda p: tuple(map(int, p.stem.split("."))), reverse=True)
    out = []
    for p in notes:
        lines = [l.rstrip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        posted = dates.get(p.stem) or datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).strftime("%Y-%m-%d")
        out.append((p.stem, lines[0], posted, lines[1:]))
    return out


def news_page(notes):
    sections = []
    for version, title, posted, lines in notes:
        body, bullets = [], []
        for line in lines + [""]:
            if line.startswith("- "):
                bullets.append(line[2:].strip())
                continue
            if bullets:
                body.append("<ul>" + "".join(f"<li>{md.inline(b, str)}</li>" for b in bullets) + "</ul>")
                bullets = []
            if line:
                body.append(f"<p>{md.inline(line.strip(), str)}</p>")
        sections.append(f'<section class="release" id="v{version}"><h2>{html.escape(title)}</h2>'
                        f'<p class="date"><time datetime="{posted}">{posted}</time> &middot; <a href="/news/{version}.txt">plain text</a></p>{"".join(body)}</section>')
    return shell.plain_page("News", "Release notes for every Fiordland Linux version, from the 0.9.0 public beta to Fiordland 1, with what changed and how to update.", "/news/",
                            "What changed in each Fiordland release. Installed systems get these with <code>tawaki update</code>.", "\n".join(sections))


def iso_version():
    """release-iso writes the ISO version into the home page, so keep whatever is there."""
    home = OUT / "index.html"
    found = re.search(r'<span id="dl-ver">([^<]*)</span>', home.read_text(encoding="utf-8")) if home.exists() else None
    return re.sub(r"-(\d+)$", r" build \1", found.group(1) if found else DEFAULT_ISO_VERSION)


def docs_index():
    blurbs = {"first-steps": "What to do after the first boot, and what Fiordland has already set up for you.",
              "updates": "Update with tawaki, choose a channel, and understand release migrations."}
    sections = []
    for group, links in shell.DOCS_GROUPS[:2]:
        cards = "".join(pages.card(title, pages.DOC_META[slug][1] if slug in pages.DOC_META else blurbs[slug], href, "Read")
                        for href, title in links for slug in [href.split("/")[2]])
        sections.append(f"<h2>{group}</h2><div class=\"cards\">{cards}</div>")
    sections.append('<h2>Help</h2><div class="cards">'
                    + pages.card("Getting help", "Where to ask, what to include and how to collect it.", "/docs/help/", "Read")
                    + pages.card("Community wiki", "Guides and fixes written by users, and a help desk.", "/wiki/", "Open the wiki") + "</div>")
    return "\n".join(sections)


notes = release_notes()
version = notes[0][0]
ctx = {"latest": (notes[0][1], notes[0][2], notes[0][3]), "ver": version, "shown": re.sub(r"(\.0)+$", "", version), "dlver": iso_version(),
       "history": [(v, title, posted, pages.RELEASE_BLURBS.get(v, "")) for v, title, posted, _ in reversed(notes)]}

main, ld = pages.home(ctx)
emit("/", shell.document("Fiordland Linux", "A Linux distribution based on Arch, with its own installer, package manager and desktop shell. Btrfs snapshots, a tested stable channel and gaming ready.",
                         "/", main, full_title=True, ld=ld))
for url, build in (("/about/", pages.about), ("/software/", pages.software), ("/download/", pages.download), ("/donate/", pages.donate)):
    title, desc, lede, inner = build(ctx)
    emit(url, shell.plain_page(title, desc, url, lede, inner))
emit("/news/", news_page(notes))

lede, body = pages.read_md("docs/why-fiordland.md")
compare_lede, compare = fragment("compare")
compare = re.sub(r'More detail: <a href="/why/">[^<]*</a>\.\s*', "", compare)
body += f'\n<section class="sec" id="compare"><h2>Compared with CachyOS and Arch</h2><p>{compare_lede}</p>{compare}</section>'
faq = json.loads((pages.CONTENT / "why-faq.json").read_text(encoding="utf-8"))
emit("/why/", shell.plain_page("Why Fiordland", "What Fiordland Linux does differently from CachyOS and Arch, what they all do, what CachyOS does better, and a side by side table.", "/why/",
                               lede, body, ld=[faq, shell.crumbs("/why/", "Why Fiordland")]))
for url, title, desc, name in (("/low-end/", "Fiordland on older PCs", "How Fiordland Linux runs on old and low end PCs: the installer switch, automatic tuning, a kernel for any 64 bit CPU and light desktops.", "low-end"),
                               ("/mirrors/", "Mirrors", "Mirrors that carry the Fiordland Linux package repo and ISOs, how to pick one, and how to host a mirror of your own.", "mirrors")):
    lede, body = fragment(name)
    emit(url, shell.plain_page(title, desc, url, lede, body))

lede, body = pages.read_md("CONTRIBUTING.md")
intro = ("<p>You do not need to write code to help. Testing and clear bug reports are some of the most useful things you can do. "
         f'Run Fiordland on a real machine and fill in the <a href="{GH}/issues/new?template=hardware.yml">hardware report</a>, open a <a href="{GH}/issues/new/choose">bug report or feature request</a>, '
         f'or ask in the <a href="{DISCORD}">Discord</a> before you start on something bigger.</p>')
emit("/contribute/", shell.plain_page("Contribute", "How to contribute to Fiordland Linux: the repository layout, how to build and test, packaging rules, conventions and the pull request process.",
                                      "/contribute/", lede, intro + "\n" + body))
lede, body = pages.read_md("SECURITY.md")
emit("/security/", shell.plain_page("Security", "The Fiordland Linux security policy: how to report a vulnerability privately, what to expect, what is in scope and how packages are signed.",
                                    "/security/", lede, body))

for slug, source in pages.DOC_SRC.items():
    title, desc = pages.DOC_META[slug]
    lede, body = pages.read_md(source)
    emit(f"/docs/{slug}/", shell.docs_page(title, desc, f"/docs/{slug}/", lede, body))
for slug, build in (("first-steps", pages.first_steps), ("updates", pages.updates), ("help", pages.helping)):
    title, desc, lede, inner = build()
    emit(f"/docs/{slug}/", shell.docs_page(title, desc, f"/docs/{slug}/", lede, inner))
emit("/docs/", shell.docs_page("Documentation", "Official guides for installing and using Fiordland Linux: install, first steps, apps with tawaki, updates, snapshots, the kernel and the crest shell.",
                               "/docs/", "Guides for installing and using Fiordland Linux. Everything here is also in the repository as plain Markdown.", docs_index()))

(OUT / "404.html").write_text(shell.plain_page("Page not found", "That page does not exist on fiordlandlinux.org.", "/404", "Nothing lives at that address.",
                                               '<ul><li><a href="/">Go to the home page</a></li><li><a href="/docs/">Read the documentation</a></li><li><a href="/download/">Download Fiordland</a></li></ul>',
                                               noindex=True, cur=""), encoding="utf-8")

order = (["/", "/download/", "/donate/", "/about/", "/software/", "/why/", "/low-end/", "/news/", "/mirrors/", "/docs/"]
         + [f"/docs/{href.split('/')[2]}/" for href in shell.DOCS_ORDER] + ["/contribute/", "/security/"])
sitemap.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                   + "".join(f"  <url><loc>{BASE}{url}</loc><lastmod>{modified[url]}</lastmod></url>\n" for url in order) + "</urlset>\n", encoding="utf-8")
