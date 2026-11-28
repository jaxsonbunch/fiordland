(() => {
const $ = id => document.getElementById(id);
const shown = v => v.replace(/-(\d+)$/, " build $1");
fetch("/iso/latest.json", { cache: "no-cache" }).then(r => (r.ok ? r.json() : null)).then(d => {
  if (!d) return;
  const raw = ((d.file.match(/^fiordland-(.+)-x86_64\.iso$/) || [])[1]) || d.date.replaceAll("-", ".");
  const ver = shown(raw);
  document.querySelectorAll("[data-iso]").forEach(a => (a.href = "/iso/" + d.file));
  if ($("dl-sum")) $("dl-sum").textContent = d.sha256;
  if ($("dl-meta")) $("dl-meta").textContent = `x86_64 \u00b7 ${(d.size / 1e9).toFixed(1)} GB \u00b7 ${ver}`;
  if ($("dl-ver")) $("dl-ver").textContent = ver;
}).catch(() => {});
const mlist = $("mirror-list");
if (mlist) {
  const CONT = {
    NA: "US CA MX GT BZ SV HN NI CR PA CU JM HT DO BS BB TT GL PR BM KY AG DM GD KN LC VC",
    SA: "BR AR CL CO PE VE EC BO PY UY GY SR",
    EU: "GB IE FR DE ES PT IT NL BE LU CH AT DK NO SE FI IS PL CZ SK HU RO BG GR HR SI RS BA ME MK AL UA BY MD LT LV EE RU CY MT AD MC LI SM",
    AS: "CN JP KR KP IN PK BD LK NP BT MM TH VN LA KH MY SG ID PH TW HK MO MN KZ UZ TM KG TJ AF IR IQ SY LB IL JO SA AE QA KW BH OM YE TR GE AM AZ BN",
    AF: "EG ZA NG KE ET GH TZ UG DZ MA TN LY SD SN CI CM AO MZ ZM ZW BW NA MG RW",
    OC: "AU NZ FJ PG NC PF WS TO"
  };
  const continentOf = code => Object.keys(CONT).find(k => CONT[k].split(" ").includes(code)) || "";
  const load = u => fetch(u, { cache: "no-store" }).then(r => (r.ok ? r.json() : null)).catch(() => null);
  Promise.all([load("/mirrors/mirrors.json"), load("/mirrors/status.json"), load("/mirrors/whoami")]).then(([list, status, who]) => {
    mlist.textContent = "";
    const rows = list?.mirrors || [];
    if (!rows.length) { mlist.textContent = "No mirrors listed yet."; return; }
    const checks = status?.mirrors || {};
    const country = /^[A-Z]{2}$/.test(who?.country || "") ? who.country : "";
    const continent = continentOf(country);
    const rank = m => {
      const s = checks[m.url.replace(/\/$/, "")];
      const near = country && m.country === country ? 0 : continent && m.continent === continent ? 1 : 2;
      return [s?.ok ? 0 : 1, near, s?.ms || 0, m.primary ? 0 : 1];
    };
    const ordered = rows.map(m => ({ m, r: rank(m) })).sort((x, y) => { for (let i = 0; i < 4; i++) if (x.r[i] !== y.r[i]) return x.r[i] - y.r[i]; return 0; });
    ordered.forEach(({ m, r }, index) => {
      const url = m.url.replace(/\/$/, "");
      const s = checks[url];
      const row = document.createElement("div");
      row.className = "mrow" + (index === 0 && s?.ok && country ? " best" : "");
      const dot = document.createElement("span");
      dot.className = "dot " + (s ? (s.ok ? "ok" : "bad") : "idle");
      dot.setAttribute("role", "img");
      dot.setAttribute("aria-label", s ? (s.ok ? "Up" : "Down") : "Unknown");
      const info = document.createElement("div");
      info.className = "minfo";
      const name = document.createElement("strong");
      name.textContent = m.name + (m.primary ? " (primary)" : "");
      if (index === 0 && s?.ok && country) {
        const tag = document.createElement("em");
        tag.textContent = r[1] === 0 ? "Closest to you" : r[1] === 1 ? "Nearest region" : "Best available";
        name.append(tag);
      }
      const sub = document.createElement("span");
      const lag = s?.ok ? (s.lag < 60 ? "up to date" : `${Math.round(s.lag / 60)} min behind`) : s ? "down" : "not checked yet";
      sub.textContent = [m.location, m.sponsor && `hosted by ${m.sponsor}`, lag].filter(Boolean).join(" · ");
      info.append(name, sub);
      const links = document.createElement("div");
      links.className = "mlinks";
      for (const [label, path] of [["Repo", "/repo/x86_64/"], ["ISO", "/iso/fiordland-latest.iso"]]) {
        const a = document.createElement("a");
        a.href = url + path;
        a.textContent = label;
        links.append(a);
      }
      row.append(dot, info, links);
      mlist.append(row);
    });
    const where = $("mirror-where");
    if (where) where.textContent = country ? `Sorted by distance to ${country} (from your connection, nothing is stored).` : "Sorted by status.";
  });
}
const badge = document.querySelector(".badge88-btn");
if (badge) {
  const msg = document.querySelector(".badge88-msg");
  const base = msg.textContent;
  let t;
  badge.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText('<a href="https://fiordlandlinux.org"><img src="https://fiordlandlinux.org/assets/fiordland-88x31.gif" width="88" height="31" alt="Powered by Fiordland Linux"></a>');
      msg.textContent = "Copied! Paste it into your site's HTML.";
    } catch {
      msg.textContent = "Couldn't copy, right-click the image to save it instead.";
    }
    clearTimeout(t);
    t = setTimeout(() => { msg.textContent = base; }, 3000);
  });
}
})();
