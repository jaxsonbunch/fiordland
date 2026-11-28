import html
import re

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
KEEP_AS_WORDS = {"x86-64-v3": "x86_64 v3", "end-4": "end 4", "GPL-3.0-only": "GPL 3.0 only", "GPL-3.0": "GPL 3.0", "SHA-256": "SHA256", "x86-64": "x86_64", "Wi-Fi": "WiFi", "wi-fi": "WiFi", "e-mail": "email"}
SKIP_TAGS = {"code", "pre", "kbd", "script", "style", "svg", "textarea"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-")


def date_words(m):
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


def plain(text, wrap=True):
    text = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", date_words, text)
    text = re.sub(r"\b(\d{4}\.\d{2}\.\d{2})-(\d+)\b", r"\1 build \2", text)
    text = text.replace("\u2014", ", ").replace("\u2013", " to ").replace("&mdash;", ", ").replace("&ndash;", " to ")
    text = re.sub(r"\s+-\s+", ", ", text)
    for a, b in KEEP_AS_WORDS.items():
        text = text.replace(a, b)

    def word(m):
        w = m.group(0)
        if wrap and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", w) and w not in PROSE:
            return f"<code>{w}</code>"
        return w.replace("-", " ")

    return re.sub(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", word, text)


PROSE = {
    "64-bit", "32-bit", "low-end", "on-screen", "out-of-tree", "real-hardware", "dual-core", "best-practice",
    "low-end", "built-in", "ten-year-old", "out-of-memory", "pre-update", "open-source", "step-by-step", "real-world", "long-term",
    "well-run", "well-known", "first-time", "full-screen", "up-to-date", "read-only", "multi-boot", "dual-boot", "so-called", "high-end",
    "end-user", "non-free", "pre-installed", "post-install", "set-up", "log-in", "sign-in", "opt-in", "opt-out", "re-sign", "e-mail",
}


def clean_html(doc):
    out, stack = [], []
    for tok in re.split(r"(<[^>]*>)", doc):
        if tok.startswith("<!") or tok.startswith("<?"):
            out.append(tok)
        elif tok.startswith("</"):
            name = tok[2:-1].strip().lower()
            if stack and stack[-1] == name:
                stack.pop()
            out.append(tok)
        elif tok.startswith("<"):
            m = re.match(r"<([a-zA-Z0-9]+)", tok)
            name = m.group(1).lower() if m else ""
            if not tok.endswith("/>") and name in SKIP_TAGS:
                stack.append(name)
            if name != "script":
                tok = re.sub(r'\b(alt|aria-label|placeholder)="([^"]*)"', lambda a: f'{a.group(1)}="{plain(a.group(2), False)}"', tok)
            out.append(tok)
        else:
            out.append(tok if stack else plain(tok))
    return "".join(out)


def clean_ld(x):
    if isinstance(x, str):
        return plain(x, False) if not x.startswith(("http", "/")) else x
    if isinstance(x, list):
        return [clean_ld(i) for i in x]
    if isinstance(x, dict):
        return {k: (v if k in ("@type", "@context", "url", "item", "@id", "sameAs") else clean_ld(v)) for k, v in x.items()}
    return x


def inline(text, link):
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{html.escape(link(html.unescape(m.group(2))), quote=True)}">{m.group(1)}</a>', p)
        out.append(p)
    return "".join(out)


def cells(row):
    row = row.strip().strip("|").replace("\\|", "\x00")
    return [c.replace("\x00", "|").strip() for c in row.split("|")]


ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def render(md, link=lambda u: u, h1=False):
    return blocks(md.replace("\r\n", "\n").split("\n"), link, h1)


def blocks(lines, link, h1):
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.lstrip().startswith("```"):
            indent = len(line) - len(line.lstrip())
            lang = line.strip()[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i][indent:] if lines[i][:indent].strip() == "" else lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre{cls}><code>{html.escape(chr(10).join(buf))}</code></pre>")
        elif re.match(r"#{1,4} ", line):
            level = len(line.split(" ")[0])
            text = line[level + 1:].strip()
            if level == 1 and not h1:
                i += 1
                continue
            tag = f"h{level}"
            out.append(f'<{tag} id="{slug(text)}">{inline(text, link)}</{tag}>')
            i += 1
        elif line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = cells(line)
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            th = "".join(f'<th scope="col">{inline(c, link)}</th>' for c in head)
            tr = "".join("<tr>" + "".join(f"<td>{inline(c, link)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
        elif ITEM.match(line):
            i, html_list = lst(lines, i, link)
            out.append(html_list)
        else:
            buf = [line.strip()]
            i += 1
            while i < n and lines[i].strip() and not lines[i].lstrip().startswith(("```", "#", "|")) and not ITEM.match(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(buf), link)}</p>")
    return "\n".join(out)


def lst(lines, i, link):
    n = len(lines)
    m = ITEM.match(lines[i])
    base = len(m.group(1))
    ordered = m.group(2)[0].isdigit()
    items = []
    while i < n:
        m = ITEM.match(lines[i])
        if not m or len(m.group(1)) != base or m.group(2)[0].isdigit() != ordered:
            break
        width = len(m.group(1)) + len(m.group(2)) + 1
        body = [m.group(3)]
        i += 1
        while i < n:
            cur = lines[i]
            if not cur.strip():
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and len(lines[j]) - len(lines[j].lstrip()) >= width:
                    body.append("")
                    i = j
                    continue
                break
            if len(cur) - len(cur.lstrip()) >= width:
                body.append(cur[width:])
                i += 1
            else:
                break
        text = blocks(body, link, False)
        if text.count("<p>") == 1 and text.startswith("<p>") and text.endswith("</p>"):
            text = text[3:-4]
        text = re.sub(r"^\[[ x]\]\s*", "", text)
        items.append(f"<li>{text}</li>")
    tag = "ol" if ordered else "ul"
    return i, f"<{tag}>" + "".join(items) + f"</{tag}>"
