(() => {
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const nav = document.querySelector(".nav");
const closeAll = () => $$(".dd.open").forEach(d => { d.classList.remove("open"); d.querySelector(".mi").setAttribute("aria-expanded", "false"); });
const burger = document.querySelector(".burger");
if (burger) burger.addEventListener("click", e => {
  e.stopPropagation();
  const on = nav.classList.toggle("open");
  burger.setAttribute("aria-expanded", on);
});
$$(".dd").forEach(dd => {
  const b = dd.querySelector(".mi");
  b.addEventListener("click", e => {
    e.stopPropagation();
    const on = !dd.classList.contains("open");
    closeAll();
    if (on) { dd.classList.add("open"); b.setAttribute("aria-expanded", "true"); }
  });
});
document.addEventListener("click", e => { if (!e.target.closest(".dd-menu")) closeAll(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") { closeAll(); if (nav) nav.classList.remove("open"); } });
$$(".zen-list").forEach(list => {
  const tabs = $$("[role=tab]", list);
  const pick = (t, focus) => tabs.forEach(x => {
    const on = x === t;
    x.setAttribute("aria-selected", on);
    x.tabIndex = on ? 0 : -1;
    const panel = document.getElementById(x.getAttribute("aria-controls"));
    panel.classList.toggle("on", on);
    panel.setAttribute("aria-hidden", String(!on));
    if (on && focus) x.focus();
  });
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => pick(t));
    t.addEventListener("keydown", e => {
      const d = e.key === "ArrowDown" ? 1 : e.key === "ArrowUp" ? -1 : 0;
      if (d) { e.preventDefault(); pick(tabs[(i + d + tabs.length) % tabs.length], true); }
    });
  });
});
const art = document.querySelector("article.dmain"), toc = document.getElementById("toc");
if (art && toc) {
  const hs = $$("h2", art);
  const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  hs.forEach(h => {
    if (!h.id) h.id = slug(h.textContent);
    const li = document.createElement("li"), a = document.createElement("a");
    a.href = "#" + h.id; a.textContent = h.textContent; li.append(a); toc.append(li);
  });
  if (!hs.length) toc.closest(".dtoc").hidden = true;
  const links = $$("a", toc);
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) links.forEach(l => l.classList.toggle("on", l.getAttribute("href") === "#" + e.target.id));
  }), { rootMargin: "-80px 0px -70% 0px" });
  hs.forEach(h => io.observe(h));
}
const q = document.getElementById("dq");
if (q) q.addEventListener("input", () => {
  const v = q.value.trim().toLowerCase();
  $$(".dside li").forEach(li => (li.hidden = !!v && !li.textContent.toLowerCase().includes(v)));
  $$(".dside .grp").forEach(g => (g.hidden = !$$("li", g).some(li => !li.hidden)));
});
})();
