/* Cozily · service worker
   - Avisos no celular.
   - Abre sem internet: a página é buscada sempre na rede primeiro (as atualizações chegam na hora)
     e só usa a cópia guardada quando não tem sinal (ex.: no mercado). */
const CACHE = "cozily-v2";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()));
const guarda = (req, res) => { if (res && (res.ok || res.type === "opaque")) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)).catch(() => {}); } return res; };
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (r.mode === "navigate" && u.origin === self.location.origin) {
    const casca = new URL("./", self.registration.scope).href;
    e.respondWith(fetch(r).then(res => guarda(casca, res)).catch(async () => (await caches.match(casca)) || Response.error()));
    return;
  }
  const fixo = (u.host === "www.gstatic.com" && u.pathname.startsWith("/firebasejs/")) || u.host === "fonts.gstatic.com" || u.host === "fonts.googleapis.com"
    || (u.origin === self.location.origin && /\.(png|svg|json)$/.test(u.pathname));
  if (fixo) e.respondWith(caches.match(r).then(m => m || fetch(r).then(res => guarda(r, res))));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const c of all) { if ("focus" in c) return c.focus(); }
    return self.clients.openWindow("./");
  })());
});
self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = { title: "Cozily", body: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(d.title || "Cozily", { body: d.body || "", icon: "icon-192.png", badge: "icon-192.png", tag: d.tag }));
});
