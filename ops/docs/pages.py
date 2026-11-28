import html
import json
import re
from pathlib import Path

import md
from shell import BASE, DISCORD, DONATE, GH, MAIL

REPO = Path(__file__).resolve().parents[2]
CONTENT = Path(__file__).resolve().parent / "content"
ORG = "https://github.com/Fiordland-Linux"
FP = "11DC 7CDC CFD3 CB71 196E  BEF1 FD69 DE77 164F 4200"

SITE_LINKS = {
    "SECURITY.md": "/security/", "CONTRIBUTING.md": "/contribute/", "rollback.md": "/docs/snapshots/", "tawaki.md": "/docs/apps/",
    "install.md": "/docs/install/", "kernel.md": "/docs/kernel/", "crest/README.md": "/docs/crest/", "live-wallpapers.md": "/docs/live-wallpapers/",
}


def link(u):
    if u.startswith(("http", "#", "/", "mailto:")):
        return u
    base, _, frag = u.partition("#")
    if base in SITE_LINKS:
        return SITE_LINKS[base] + ("#" + frag if frag else "")
    return f"{GH}/blob/main/{base}"


LINK_NAMES = {"tawaki.md": "tawaki guide", "rollback.md": "snapshots and rollback", "SECURITY.md": "security policy", "CONTRIBUTING.md": "contributing guide",
              "install.md": "install guide", "kernel.md": "kernel guide"}


def names(text):
    """Links in the Markdown docs are written with file names, which mean nothing on a website."""
    return re.sub(r"(<a href=\"[^\"]*\">)([^<]*\.md)(</a>)", lambda m: m.group(1) + LINK_NAMES.get(m.group(2), m.group(2)) + m.group(3), text)


def read_md(rel):
    text = (REPO / rel).read_text(encoding="utf-8")
    text = re.sub(r"\s*The same (page|steps) (is|are) on the website at \[[^\]]*\]\([^)]*\)\.", "", text)
    lines = text.split("\n")
    first = next(i for i, l in enumerate(lines) if l.strip() and not l.startswith("#"))
    j = first
    while j < len(lines) and lines[j].strip():
        j += 1
    lede = md.inline(" ".join(l.strip() for l in lines[first:j]), link)
    return names(lede), names(md.render("\n".join(lines[:first] + lines[j:]), link))


def esc(s):
    return html.escape(s, quote=True)


def card(title, text, href, more):
    return f'<article class="card"><h3>{title}</h3><p>{text}</p><a class="more" href="{href}">{more}</a></article>'


def term(text):
    return f'<pre class="term"><code>{esc(text)}</code></pre>'


def pkg(name):
    src = (REPO / "packages" / name / "PKGBUILD").read_text(encoding="utf-8")
    var = dict(re.findall(r"^(_?[a-z]+)=([^\n$]+)$", src, re.M))
    ver = re.search(r"^pkgver=(.*)$", src, re.M).group(1).strip("\"'")
    ver = re.sub(r"\$\{?(_?\w+)\}?", lambda m: var.get(m.group(1), "").strip("\"'"), ver)
    desc = re.search(r"^pkgdesc=(.*)$", src, re.M).group(1).strip("\"'")
    return ver, desc


RELEASE_BLURBS = {
    "0.9.0": "Updates carry system changes, so an install keeps up with new ISOs. New installs use GRUB with snapshots you can boot, and the installer can put Fiordland next to Windows.",
    "0.9.1": "A tested stable channel, gaming packages that come with Fiordland, and an installer that cleans up and shows the reason when something fails.",
    "1.0.0": "Out of beta, with the Fiordland kernel, crest 1, tawaki 1.0, Kuaka 1.0, weka 1.1, a redesigned installer, faster boot, shutdowns that no longer hang and automatic tuning for weak hardware.",
}


def home(ctx):
    ver, shown, dlver = ctx["ver"], ctx["shown"], ctx["dlver"]
    zen = [
        ("tawaki", "tawaki", "One command for the Arch repos, Flathub and the AUR. It installs from the cleanest source and skips Flatpaks that would pull in a large runtime.",
         term("tawaki install firefox steam\ntawaki search obs\ntawaki update\ntawaki install foo --from aur") +
         '<p>Packages are looked up in all three sources at once. A prebuilt package is preferred over a Flatpak that would pull in a large runtime you do not have yet.</p><a class="more" href="/docs/apps/">Read the tawaki guide</a>'),
        ("rawaru", "rawaru installer", "A graphical installer. Choose from 11 desktops and 13 window managers, install next to Windows or on a whole disk, and get Btrfs snapshots, zram and the right GPU driver.",
         '<img src="/assets/shots/installer.webp?v=2" alt="The rawaru installer on the desktop step, with Hyprland and its shell options" width="1920" height="1080" loading="lazy"><a class="more" href="/docs/install/">Read the install guide</a>'),
        ("crest", "crest", "The Fiordland shell for Hyprland, built on Quickshell: bar, dashboard, launcher, lock screen and settings, with colors taken from your wallpaper.",
         '<img src="/assets/shots/hyprland.webp?v=2" alt="Hyprland with crest, the Fiordland shell, showing its dashboard over kitty and Thunar" width="1920" height="1080" loading="lazy"><a class="more" href="/docs/crest/">About crest</a>'),
        ("plasma", "KDE Plasma", "The default live session and desktop, with Breeze Dark. Pick any of 24 desktops and window managers in the installer, or swap later with the Desktops app.",
         '<img src="/assets/shots/plasma.webp?v=2" alt="KDE Plasma with Breeze Dark, Dolphin and Konsole running tawaki search" width="1920" height="1080" loading="lazy"><a class="more" href="/software/">See all the software</a>'),
        ("niri", "niri with Noctalia", "Scrollable tiling on Wayland with the Noctalia shell, one of the dotfile sets the installer can set up for you.",
         '<img src="/assets/shots/niri.webp?v=2" alt="niri with the Noctalia bar, tawaki search results and btop in two columns" width="1920" height="1080" loading="lazy"><a class="more" href="/software/">See all the software</a>'),
    ]
    tabs = "".join(
        f'<button class="zt" role="tab" id="t-{k}" aria-controls="p-{k}" aria-selected="{"true" if i == 0 else "false"}"{"" if i == 0 else " tabindex=\"-1\""}><b>{t}</b><span class="zd"><span class="zi">{d}</span></span></button>'
        for i, (k, t, d, _) in enumerate(zen))
    panels = "".join(f'<div class="zp{" on" if i == 0 else ""}" role="tabpanel" id="p-{k}" aria-labelledby="t-{k}" aria-hidden="{"false" if i == 0 else "true"}">{body}</div>' for i, (k, _, _, body) in enumerate(zen))
    latest_title, latest_date, latest_lines = ctx["latest"]
    latest = "".join(f"<li>{md.inline(l[2:].strip(), str)}</li>" for l in [x for x in latest_lines if x.startswith("- ")][:4])
    main = f"""<main id="main">
<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-copy">
      <a class="badge" href="/news/#v{ver}"><span class="dot"></span><span class="shine">Fiordland {shown} &middot; <span id="dl-ver">{dlver}</span></span></a>
      <h1>Fiordland Linux</h1>
      <p class="lede">Based on Arch, with its own installer, package manager and desktop shell. Its own kernel built on CachyOS, Btrfs snapshots and Flathub set up from the start. Steam, MangoHud and gamescope come installed.</p>
      <div class="cta"><a class="btn" href="/download/">Download</a><a class="btn ghost" href="/why/">Why Fiordland</a></div>
      <p class="meta" id="dl-meta">x86_64 &middot; about 3 GB</p>
    </div>
    <div class="laptop"><div class="lid"><img src="/assets/shots/plasma.webp" alt="The Fiordland live session: KDE Plasma with Breeze Dark, Dolphin and Konsole running tawaki search" width="1920" height="1080"></div><div class="base"></div></div>
  </div>
  <svg class="edge" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true"><path class="to-light" d="M0 52C180 92 360 94 560 62C760 30 940 8 1140 30C1260 43 1360 60 1440 52V90H0Z"/></svg>
</section>
<section class="band" id="inside" aria-labelledby="inside-h">
  <div class="wrap">
    <h2 id="inside-h">What is inside</h2>
    <p class="sub">Fiordland ships its own installer, package manager and shell. Pick a part to see it.</p>
    <div class="zen-grid">
      <div class="zen-list" role="tablist" aria-orientation="vertical" aria-label="Parts of Fiordland">{tabs}</div>
      <div class="zen-view">{panels}</div>
    </div>
  </div>
  <svg class="edge" viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true"><path class="to-base" d="M0 80V50L110 34L200 54L330 16L440 46L560 28L690 60L800 24L930 52L1040 20L1170 50L1290 30L1440 56V80Z"/></svg>
</section>
<section class="plain-sec" id="latest" aria-labelledby="latest-h">
  <div class="wrap split">
    <div><h2 id="latest-h">{html.escape(latest_title)}</h2><p class="sub"><time datetime="{latest_date}">{latest_date}</time></p><a class="more" href="/news/">Read the release notes</a></div>
    <ul class="news-list">{latest}</ul>
  </div>
</section>
</main>"""
    ld = [
        {"@type": "Organization", "@id": BASE + "/#org", "name": "Fiordland Linux", "url": BASE + "/", "logo": BASE + "/assets/brand/icon-512.png",
         "founder": {"@type": "Person", "name": "Apollo", "url": "https://apollo44.lat", "sameAs": ["https://github.com/3cfl"]}, "sameAs": [ORG, DISCORD]},
        {"@type": "WebSite", "@id": BASE + "/#site", "url": BASE + "/", "name": "Fiordland Linux", "publisher": {"@id": BASE + "/#org"}},
        {"@type": "SoftwareApplication", "name": "Fiordland Linux", "applicationCategory": "OperatingSystem", "operatingSystem": "Linux", "softwareVersion": ctx["ver"],
         "license": "https://www.gnu.org/licenses/gpl-3.0.html", "downloadUrl": BASE + "/download/", "url": BASE + "/", "image": BASE + "/assets/og.png",
         "description": "A Linux distribution based on Arch, with its own installer, package manager and desktop shell.", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
    ]
    return main, ld


def about(ctx):
    rel = "".join(
        f'<li><time datetime="{d}">{md.date_words(re.match(r"(\d{4})-(\d{2})-(\d{2})", d))}</time><div><b>{t}</b><p>{blurb}</p></div></li>'
        for _, t, d, blurb in ctx["history"])
    parts = [
        ("tawaki", "package manager", "tawaki", "Installs, removes and updates software from pacman, Flathub and the AUR with one command."),
        ("rawaru", "installer", "rawaru", "A graphical installer with 11 desktops, 13 window managers, Btrfs and dual boot with Windows."),
        ("crest", "desktop shell", "crest", "The Hyprland shell, written in plain QML for Quickshell."),
        ("Kuaka", "update app", "kuaka", "Shows pending updates, applies them in one click and puts the system back to a snapshot if one goes wrong."),
        ("weka", "Desktops app", "weka", "Adds, removes and swaps desktops and window managers cleanly, without reinstalling."),
    ]
    rows = "".join(f'<tr><th scope="row"><a href="{ORG}/{r}">{n}</a></th><td>{kind}</td><td>{d}</td></tr>' for n, kind, r, d in parts)
    inner = f"""
<section class="sec">
<h2>What Fiordland is</h2>
<p>Fiordland Linux is a Linux distribution based on Arch Linux. It installs a complete desktop in a few clicks, keeps itself current with a tested stable channel, and takes a Btrfs snapshot before every update so a bad one can be undone. The installer, the package manager, the update app and the desktop shell are all written for Fiordland rather than borrowed.</p>
<p>It is aimed at people who want Arch packages and a fast kernel without assembling the system by hand: new Linux users coming from Windows, gamers, and anyone with an older machine that deserves a second life. The same install adapts to the hardware it lands on.</p>
</section>
<section class="sec">
<h2>The name and the logo</h2>
<p>The Fiordland penguin, called tawaki in Maori, is a crested penguin that lives in the rainforests of the south west of New Zealand. The logo is a tawaki: the yellow stripe is its crest and the terminal prompt is its eye.</p>
</section>
<section class="sec">
<h2>History</h2>
<ol class="timeline">{rel}</ol>
<p>Fiordland 1 is the first release out of beta. Installed systems move to it with a normal update, and nothing needs reinstalling. Read the full <a href="/news/">release notes</a>.</p>
</section>
<section class="sec">
<h2>What it is made of</h2>
<div class="tbl"><table><thead><tr><th scope="col">Part</th><th scope="col">Role</th><th scope="col">What it does</th></tr></thead><tbody>{rows}
<tr><th scope="row"><a href="/docs/kernel/">The Fiordland kernel</a></th><td>kernel</td><td>A fork of the CachyOS kernel packaging with the BORE scheduler and BBRv3, built for the x86_64 baseline so it runs on any 64 bit CPU.</td></tr></tbody></table></div>
<p>The <a href="/software/">software page</a> has versions, languages and source links for every part.</p>
</section>
<section class="sec">
<h2>Who makes it</h2>
<p>Fiordland Linux was created by <a href="https://apollo44.lat">Apollo</a> (<a href="https://github.com/3cfl">3cfl</a> on GitHub, u5sk on Discord), who designs and maintains it, with help from the contributors listed on GitHub. It is developed in the open: every package, the installer, the website and the build scripts live in the <a href="{GH}">Fiordland repository</a>, and the license is GPL 3.0. See <a href="/contribute/">how to contribute</a> if you want to help. The website was designed by taz (<a href="https://github.com/jaxsonbunch">jaxsonbunch</a> on GitHub).</p>
</section>
<section class="sec">
<h2>Built on the work of others</h2>
<ul>
<li><a href="https://archlinux.org">Arch Linux</a> and its package repositories, the base of everything.</li>
<li><a href="https://cachyos.org">CachyOS</a>, whose <a href="https://github.com/CachyOS/linux-cachyos">kernel packaging</a> the Fiordland kernel is forked from, and whose Proton and Wine builds ship in the gaming package.</li>
<li><a href="https://quickshell.org">Quickshell</a> by outfoxxed and contributors, which crest is built on. crest 1 draws on the <a href="https://github.com/end-4/dots-hyprland">Hyprland dotfiles</a> by end 4, and the earlier crest was forked from <a href="https://github.com/caelestia-dots/shell">Caelestia shell</a>. Both are GPL 3.0.</li>
<li><a href="https://gitlab.archlinux.org/archlinux/archiso">archiso</a>, the base of the live ISO.</li>
<li>The maintainers of the AUR packages bundled in the repository.</li>
</ul>
</section>
<section class="sec">
<h2>Contact</h2>
<p>For bugs and ideas, use <a href="{GH}/issues/new/choose">GitHub issues</a>. For questions, the <a href="{DISCORD}">Discord</a> and the wiki <a href="/wiki/Help_desk">help desk</a> are the fastest. For anything else, write to <a href="mailto:{MAIL}">{MAIL}</a>. Security problems go through the <a href="/security/">security policy</a>.</p>
</section>"""
    return ("About Fiordland", "What Fiordland Linux is, how it got its name, how it grew from a beta to Fiordland 1, who makes it and what it is made of.",
            "A distribution based on Arch, made in the open, with its own installer, package manager, update app and desktop shell.", inner)


PROJECTS = [
    ("Applications", [
        ("tawaki", "tawaki", "Package manager", "Installs, removes, searches and updates software from pacman, Flathub and the AUR with one command, picking the cleanest source. Looks in all three at once and warns before building from the AUR.", "Rust", ORG + "/tawaki", "/docs/apps/"),
        ("rawaru", "rawaru", "Installer", "The graphical installer on the live ISO. Whole disk, next to Windows or your own partitions, Btrfs with snapshots, GRUB on UEFI and BIOS, GPU driver detection and a choice of 11 desktops and 13 window managers.", "Python, PySide6 and QML", ORG + "/rawaru", "/docs/install/"),
        ("kuaka", "kuaka", "Update app", "Shows what is waiting, updates system packages and Flatpaks in one click, marks updates that need a restart, and undoes an update from its history tab through snapshots.", "Rust and Slint", ORG + "/kuaka", "/docs/updates/"),
        ("weka", "weka", "Desktops app", "Adds, removes and swaps desktops and window managers, sets up the login manager and removes what the old one left behind.", "Python, PySide6 and QML", ORG + "/weka", "/docs/first-steps/"),
        ("crest", "crest", "Desktop shell", "The Hyprland shell: bar, launcher, notifications, dashboard, quick settings, lock screen, overview and settings, in plain QML with no C++ plugin. Includes the greetd login screen, crest greeter.", "QML on Quickshell", GH + "/tree/main/crest", "/docs/crest/"),
        ("kereru", "Kereru", "Live wallpapers", "An optional extra that plays Wallpaper Engine wallpapers you own on Steam, with a picker, a tray icon and a sandboxed engine.", "Rust and Slint", GH + "/tree/main/kereru", "/docs/live-wallpapers/"),
    ]),
    ("System packages", [
        ("linux-fiord", "The Fiordland kernel", "Kernel", "A fork of the CachyOS kernel packaging with the BORE scheduler, a 1000 Hz timer, BBRv3 and NTSYNC built in, targeting the x86_64 baseline so it runs on older CPUs.", "Arch package", GH + "/tree/main/packages/linux-fiord", "/docs/kernel/"),
        ("fiordland-base", "fiordland base", "Release and migrations", "The release itself: core packages, the fiordland command, release notes and numbered system migrations that bring installed systems up to date without a reinstall.", "Arch package", GH + "/tree/main/packages/fiordland-base", "/docs/updates/"),
        ("fiordland-tune", "fiordland tune", "Hardware profiles", "Picks low end, balanced or performance settings by itself from the memory, CPU threads and graphics of the machine, and lets you choose by hand.", "Arch package", GH + "/tree/main/packages/fiordland-tune", "/low-end/"),
        ("fiordland-desktop", "fiordland desktop", "Defaults and branding", "Desktop defaults and branding for Fiordland.", "Arch package", GH + "/tree/main/packages/fiordland-desktop", None),
        ("fiordland-gaming", "fiordland gaming", "Gaming packages", "A meta package: Steam, the CachyOS builds of Proton and Wine, umu launcher, protontricks, winetricks, gamemode, MangoHud and gamescope. Remove it in one command if you do not play.", "Arch package", GH + "/tree/main/packages/fiordland-gaming", "/docs/first-steps/"),
        ("fiordland-dev", "fiordland dev", "Developer tools", "An opt in meta package for programming: base-devel, git, github-cli, cmake, meson, clang, gdb, Python with pip, Node.js, Go, OpenJDK, podman and more. Install it with <code>tawaki install fiordland-dev</code>.", "Arch package", GH + "/tree/main/packages/fiordland-dev", None),
        ("fiordland-keyring", "fiordland keyring", "Signing key", "The public key that every package and the repository database are signed with.", "Arch package", GH + "/tree/main/packages/fiordland-keyring", "/security/"),
    ]),
]


def software(ctx):
    out = []
    for group, items in PROJECTS:
        rows = []
        for pk, name, role, text, lang, src, docs in items:
            ver, _ = pkg(pk)
            rows.append(f'<article class="proj"><div class="proj-h"><h3>{name}</h3><span class="tag">{role}</span><span class="ver">{esc(ver)}</span></div><p>{text}</p>'
                        f'<p class="links"><span>{esc(lang)}</span><a href="{src}">Source</a>{f"<a href={chr(34)}{docs}{chr(34)}>Documentation</a>" if docs else ""}</p></article>')
        out.append(f'<section class="sec"><h2>{group}</h2><div class="projs">{"".join(rows)}</div></section>')
    inner = "".join(out) + f"""
<section class="sec">
<h2>Licenses and source</h2>
<p>Fiordland's own software is licensed GPL 3.0. The kernel and other upstream software keep their own licenses. The main repository holds crest, the packaging, the ISO profile, the website and the build tools. tawaki, rawaru, kuaka and weka live in their own repositories under the <a href="{ORG}">Fiordland Linux organization</a> on GitHub, and the main repository packages their tagged releases. Versions above are read from the package build files, so they match what is in the repo.</p>
</section>
<section class="sec">
<h2>Desktops and window managers</h2>
<p>The installer offers 11 desktops: KDE Plasma (the default), GNOME, COSMIC, Xfce, Cinnamon, Budgie, MATE, LXQt, Deepin, Enlightenment and LXDE. It offers 13 window managers: Hyprland, niri, Sway, labwc, i3, bspwm, awesome, Qtile, xmonad, herbstluftwm, Openbox, Fluxbox and IceWM.</p>
<p>Some choices offer dotfile sets that bring their own setup: the Fiordland shell (crest), Noctalia, Dux Shell, Caelestia, illogical impulse, HyDE, ML4W, JaKooLit and iNiR.</p>
</section>"""
    return ("Software", "Every part of Fiordland Linux: the tawaki package manager, rawaru installer, crest shell, Kuaka and weka apps, the kernel and system packages.",
            "The parts Fiordland is made of, with their versions, languages, source and documentation.", inner)


def donate(ctx):
    inner = f"""
<section class="sec">
<h2>Fiordland is free</h2>
<p>Fiordland Linux is free and open source under the GPL 3.0, and nothing is locked behind a donation. If you want to chip in anyway, you can donate through Stripe.</p>
<div class="cta"><a class="btn" href="{DONATE}">Donate with Stripe</a></div>
<p class="note">The button opens a page hosted by Stripe. For questions about a donation, write to <a href="mailto:{MAIL}">{MAIL}</a>.</p>
</section>
<section class="sec">
<h2>Other ways to help</h2>
<p>Money is not the only thing that helps.</p>
<ul>
<li><b>Test and report.</b> Run Fiordland on a real machine and fill in the <a href="{GH}/issues/new?template=hardware.yml">hardware report</a>.</li>
<li><b>Improve the docs.</b> The guides are plain Markdown in the repository, and this site is generated from them.</li>
<li><b>Send code.</b> Start with the <a href="/contribute/">contributing guide</a>.</li>
<li><b>Report a security problem</b> privately, following the <a href="/security/">security policy</a>.</li>
<li><b>Tell someone</b> who might like Fiordland about it.</li>
</ul>
</section>"""
    return ("Donate", "Support Fiordland Linux with a donation through Stripe. It is free and open source, and there are other ways to help with testing, docs and code.",
            "Fiordland is free. Donations are optional.", inner)


def download(ctx):
    inner = f"""
<div class="dlbox">
  <div><h2>Fiordland {ctx["shown"]}</h2><p class="meta" id="dl-meta">x86_64 &middot; about 3 GB</p></div>
  <a class="btn" data-iso href="/iso/fiordland-latest.iso">Download the ISO</a>
</div>
<section class="sec">
<h2>Check your download</h2>
<p>The SHA256 checksum of the latest ISO is below, so you can check the file arrived intact.</p>
<pre class="term" id="dl-sum" tabindex="0"><code>Checking...</code></pre>
<p>Compare it with the checksum of your file:</p>
<div class="tbl"><table><thead><tr><th scope="col">System</th><th scope="col">Command</th></tr></thead><tbody>
<tr><th scope="row">Linux</th><td><code>sha256sum fiordland-*.iso</code></td></tr>
<tr><th scope="row">macOS</th><td><code>shasum -a 256 fiordland-*.iso</code></td></tr>
<tr><th scope="row">Windows (PowerShell)</th><td><code>Get-FileHash fiordland-*.iso</code></td></tr>
</tbody></table></div>
<p>Packages and the repository database are signed. The signing key is <code>{FP}</code>, and the <a href="/security/#package-signing">security page</a> explains how it is used.</p>
</section>
<section class="sec">
<h2>What you need</h2>
<div class="tbl"><table><tbody>
<tr><th scope="row">Processor</th><td>Any 64 bit x86 PC. UEFI is recommended, older BIOS machines work too.</td></tr>
<tr><th scope="row">Memory</th><td>4 GB at least, 8 GB or more is better.</td></tr>
<tr><th scope="row">Disk</th><td>30 GB, either a whole disk (which is erased) or free room next to Windows on a UEFI computer.</td></tr>
<tr><th scope="row">USB stick</th><td>4 GB or more.</td></tr>
<tr><th scope="row">Network</th><td>An internet connection during the install. Packages are downloaded fresh, so you get current software.</td></tr>
<tr><th scope="row">Secure Boot</th><td>Turn it off in the firmware settings first. Fiordland's boot files are not signed yet.</td></tr>
</tbody></table></div>
<p>Back up anything you want to keep before you start. Installing on a whole disk removes everything on it.</p>
</section>
<section class="sec">
<h2>Four steps to a working desktop</h2>
<ol class="steps">
<li><b>Write the ISO to a USB stick</b> with <a href="https://rufus.ie">Rufus</a> in DD image mode, <a href="https://etcher.balena.io">balenaEtcher</a>, or <code>dd</code> on Linux.</li>
<li><b>Boot from the stick.</b> Open the boot menu while the logo shows (usually F12, F11, F8, Esc or F2) and pick Fiordland Linux live.</li>
<li><b>Try it first if you like.</b> The live session runs KDE Plasma and starts the installer by itself. You are logged in as <code>fiord</code> with no password, and nothing is written to your disks until you press Install on the Review page.</li>
<li><b>Install.</b> Work through five pages: region, disk, account, desktop and review. It takes 5 to 20 minutes depending on your connection.</li>
</ol>
<p>The <a href="/docs/install/">install guide</a> covers every page of the installer, installing next to Windows, and what to do if the disk does not show up.</p>
</section>
<section class="sec">
<h2>Other ways to get it</h2>
<ul>
<li><a href="/mirrors/">Mirrors</a> carry the ISO and the package repository, and you can host one yourself.</li>
<li>In the Discord, run <code>/iso</code> for the latest link and checksum.</li>
<li>Installed systems use the package repository at <code>https://fiordlandlinux.org/repo/x86_64</code>. <a href="/repo/x86_64/">Browse it</a>.</li>
<li>An installed system does not need a newer ISO: <a href="/docs/updates/">updates</a> bring the same changes.</li>
</ul>
</section>"""
    return ("Download Fiordland Linux", "Download the Fiordland Linux ISO, check its SHA256 checksum, see the system requirements and follow four steps from a USB stick to a working desktop.",
            "The ISO boots a live KDE Plasma session and starts the installer. You can try Fiordland before anything is written to your disks.", inner)


DOC_META = {
    "install": ("Install Fiordland", "Install Fiordland Linux from a download to a working desktop: the USB stick, booting, every page of the installer, installing next to Windows and fixes."),
    "apps": ("Installing apps", "Install, remove, search and update software with tawaki, which uses pacman, Flathub and the AUR, with its settings, update channels and AUR safety notes."),
    "snapshots": ("Snapshots and rollback", "Undo a bad update on Fiordland Linux with Btrfs snapshots, from a running system or from the GRUB menu when it does not boot."),
    "kernel": ("The Fiordland kernel", "What the Fiordland kernel changes from CachyOS and Arch, why, how to switch to it and back, how to build it and how to change its behaviour at runtime."),
    "crest": ("The crest shell", "The crest Hyprland shell: what is in it, how its colors and low end mode work, how to run it, its keyboard shortcuts and its IPC commands."),
    "live-wallpapers": ("Live wallpapers", "Play Wallpaper Engine wallpapers on Fiordland with Kereru: setup, the picker, the Steam Workshop tab, pausing, sandboxing and fixes."),
}
DOC_SRC = {"install": "docs/install.md", "apps": "docs/tawaki.md", "snapshots": "docs/rollback.md", "kernel": "docs/kernel.md", "crest": "crest/README.md", "live-wallpapers": "docs/live-wallpapers.md"}


def first_steps():
    inner = f"""
<h2>Connect to the internet</h2>
<p>Click the network icon in the panel and pick your WiFi. A cable works without any setup.</p>
<h2>Update once</h2>
<p>The ISO may be a few days old. Open a terminal and run:</p>
{term("tawaki update")}
<p>It asks for your password, then updates the system, AUR packages and Flatpaks together. If the Fiordland release number changes, it prints it with the release notes. Close games and apps first, and restart afterwards if the kernel was updated.</p>
<h2>Install your apps</h2>
<p>Use tawaki from the terminal. It finds the cleanest source for each app, and <code>i</code> is a shortcut for <code>install</code>:</p>
{term("tawaki install firefox steam discord")}
<p>The <a href="/docs/apps/">apps guide</a> covers search, removing, sources and settings. Flathub is already set up, so Flatpak apps work straight away.</p>
<h2>Already set up for you</h2>
<ul>
<li>Graphics drivers for your GPU, Vulkan, and 32 bit libraries for Steam and Wine.</li>
<li>Steam, the CachyOS builds of Proton and Wine, umu launcher, gamemode, MangoHud and gamescope. Remove them with <code>sudo pacman -Rns fiordland-gaming</code> if you do not play.</li>
<li>Btrfs with automatic snapshots before every update, so a bad update can be <a href="/docs/snapshots/">undone</a>.</li>
<li>Printing with network printers found automatically, Bluetooth, power profiles, firmware updates and zram swap.</li>
<li>A firewall (ufw) that blocks incoming connections, and encrypted DNS one command away with <code>sudo fiordland dns tls</code>.</li>
<li>GRUB, with other systems found by os-prober. On a dual boot, the menu lists both Fiordland and Windows.</li>
</ul>
<h2>Pair Bluetooth devices</h2>
<p>On the crest desktop, open quick settings and click the arrow on the Bluetooth tile. Put the device in pairing mode and click it under <b>available</b>. If it shows a code or needs a PIN, crest asks for it. Other desktops have their own Bluetooth settings.</p>
<h2>Make it yours</h2>
<ul>
<li><b>Change desktop.</b> Open Desktops (<code>weka</code>) to add, remove or swap desktops and window managers without reinstalling.</li>
<li><b>Choose a kernel.</b> The CachyOS kernel is the default and the Arch kernel stays as a backup. To try the <a href="/docs/kernel/">Fiordland kernel</a>, run <code>sudo fiordland kernel fiord</code>.</li>
<li><b>Pick a channel.</b> Stable is the default. <code>fiordland-channel rolling</code> gets packages the day Arch releases them.</li>
<li><b>Tune for the machine.</b> Fiordland picks lighter settings on weak hardware by itself. <code>fiordland-tune status</code> shows what is in use, and <code>sudo fiordland-tune apply low-end</code>, <code>balanced</code> or <code>performance</code> chooses by hand.</li>
<li><b>Live wallpapers.</b> If you own Wallpaper Engine on Steam, <a href="/docs/live-wallpapers/">Kereru</a> plays your wallpapers.</li>
</ul>
<h2>Terminal basics</h2>
<ul>
<li><code>sudo</code> runs a command as administrator. It asks for your own password.</li>
<li>Typing a command you do not have tells you which package provides it.</li>
<li><code>Ctrl+C</code> stops a running command. <code>Ctrl+Shift+V</code> pastes in most terminals.</li>
<li><code>fiordland version</code> shows your release, and <code>fiordland news</code> shows what changed.</li>
</ul>"""
    return ("First steps", "What to do after the first boot of Fiordland Linux: connect, update once, install apps, learn what is already set up and how to tune it.",
            "What to do after the first boot, and what Fiordland has already done for you.", inner)


def updates():
    inner = f"""
<h2>Update</h2>
{term("tawaki update")}
<p>Run it every week or two. It counts what is waiting in each source, asks before it starts, then updates the system with <code>pacman -Syu</code>, then AUR packages, then Flatpaks. To look without installing anything, run <code>tawaki check</code>.</p>
<p>The Kuaka update app does the same with a window. It groups updates, marks the ones that need a restart, shows release notes and Arch news, and has a history tab with an Undo button for every snapshot taken before a change. With <code>kuaka --tray</code> it checks in the background every 6 hours by default and notifies at most once a day.</p>
<h2>Channels</h2>
<p>Arch packages arrive through one of two channels. <b>Stable</b> is a snapshot of the Arch repos that moves forward every two weeks, after Fiordland's install, update and boot tests pass, and security fixes arrive sooner. <b>Rolling</b> gets packages the day Arch releases them, which is newer and less tested. Stable is the default.</p>
{term("fiordland-channel\nfiordland-channel rolling\nfiordland-channel stable")}
<p>Without an argument it prints the current channel. With one it switches, then run <code>tawaki update</code> to sync.</p>
<h2>New releases</h2>
<p>A new ISO is only for new installs. An installed system gets the same changes through <code>tawaki update</code>: new default packages, settings and fixes ship as numbered migrations in <code>fiordland-base</code>. Each runs once, after the pre update snapshot, and is written to be safe to run twice. When the release number changes, the update prints it with a short list of what is new, for example <code>Fiordland 0.9.0 -> 1.0.0</code>.</p>
<ul>
<li><code>fiordland version</code> shows the current release, and <code>fiordland news</code> shows the notes. <code>cat /etc/os-release</code> works too.</li>
<li><code>fiordland-migrate --list</code> shows which release changes are applied.</li>
<li>A change that fails is reported, logged in <code>/var/log/fiordland-migrate.log</code> and tried again on the next update.</li>
<li>All release notes are on the <a href="/news/">news page</a>.</li>
</ul>
<h2>Before updating</h2>
<ul>
<li>Close games and apps that are running, and keep a laptop plugged in.</li>
<li>Read what the update prints. Messages that start with <code>==></code> or <code>warning:</code> sometimes ask you to do something.</li>
<li>Updates to the kernel, firmware, systemd, glibc, Mesa and NVIDIA drivers need a restart to take effect. Until then, new USB devices and some drivers may not load.</li>
</ul>
<h2>When an update goes wrong</h2>
<p>A snapshot is taken before every update, so you can go back. See <a href="/docs/snapshots/">snapshots and rollback</a>. If the desktop does not start, pick the Arch kernel or safe graphics in the boot menu first, or boot an older snapshot from the Fiordland snapshots entry. Each snapshot includes its own kernel, so this also undoes a bad kernel update.</p>
<h2>Clean up</h2>
<p>Old package downloads are cleared every week automatically, keeping the last three versions. To remove packages nothing uses any more:</p>
{term("sudo pacman -Rns $(pacman -Qdtq)")}
<p>Snapshots from updates are trimmed to the newest 10, and Btrfs is scrubbed monthly.</p>"""
    return ("Updates", "How updates work on Fiordland Linux: tawaki update, the stable and rolling channels, release migrations, the Kuaka update app and going back.",
            "Fiordland is a rolling release. Packages update in small steps, and new releases arrive the same way.", inner)


def helping():
    inner = f"""
<h2>Where to ask</h2>
<ul>
<li><a href="/wiki/">Wiki</a>: guides and fixes written by users. Search it first, especially the <a href="/wiki/Troubleshooting">Troubleshooting</a> and <a href="/wiki/FAQ">FAQ</a> pages.</li>
<li><a href="/wiki/Help_desk">Help desk</a>: ask a question on the wiki. Every wiki page also has a Discussion tab.</li>
<li><a href="{DISCORD}">Discord</a>: chat with other users. Run <code>/helpme</code> to see what to include.</li>
<li><a href="{GH}/issues/new/choose">GitHub issues</a>: bugs in Fiordland, tawaki or the installer, with a form for bug reports, feature requests and hardware reports.</li>
<li><a href="https://wiki.archlinux.org">Arch Wiki</a>: Fiordland uses the Arch repos, so most of it applies.</li>
</ul>
<h2>What to include</h2>
<p>What you did, what you expected, and what happened instead. The exact error text, copied rather than retyped. Your hardware, especially the GPU.</p>
<p>Fiordland can collect the details for you. This writes one file in your home folder with your user and host names replaced, and nothing is uploaded:</p>
{term("fiordland report")}
<p>To print a hardware summary you can paste, or the errors from the current boot:</p>
{term("inxi -Fxz\njournalctl -b -p err --no-pager | tail -50")}
<h2>If the installer fails</h2>
<p>Press Save log on the failure page, then try again from the Review page. Attach the log to a bug report. Other install problems are covered at the end of the <a href="/docs/install/">install guide</a>.</p>
<h2>Do not paste</h2>
<p>Passwords, WiFi keys or anything from <code>/etc/shadow</code>. <code>inxi -z</code> already hides serial numbers and IP addresses. For a security problem, do not open a public issue: follow the <a href="/security/">security policy</a>.</p>"""
    return ("Getting help", "Where to ask for help with Fiordland Linux, what to include in a question, the fiordland report command and what not to paste.",
            "Where to ask, what to include, and how to collect it.", inner)
