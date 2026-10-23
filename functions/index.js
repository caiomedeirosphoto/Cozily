/* Robô de ofertas do Cozily (Cloud Functions, plano Blaze).
   - rodadaDiaria: todo dia às 6h procura o que falta nas casas, escolhe as ofertas e publica.
   - checagemHoraria: de hora em hora testa os links publicados e tira o que acabou.
   - comissoesDiarias: às 7h atualiza as comissões do mês no painel.
   - comandoDoPainel: "Rodar agora" no painel.
   Os códigos de afiliado ficam nos segredos do Firebase (nunca no código nem no app). */
const { onSchedule } = require("firebase-functions/v2/scheduler");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");
const { defineSecret } = require("firebase-functions/params");
const { setGlobalOptions, logger } = require("firebase-functions/v2");
const admin = require("firebase-admin");
const core = require("./core");
const LOJAS = [require("./lojas/shopee"), require("./lojas/mercadolivre"), require("./lojas/amazon")];

admin.initializeApp();
const db = admin.firestore();
setGlobalOptions({ region: "southamerica-east1", maxInstances: 1 });

const NOMES_SEGREDOS = [...new Set(LOJAS.flatMap(l => l.segredos))];
const SEGREDOS = NOMES_SEGREDOS.map(n => defineSecret(n));
const lerSegredos = () => Object.fromEntries(SEGREDOS.map((s, i) => { let v = ""; try { v = s.value() || ""; } catch (e) { v = ""; } return [NOMES_SEGREDOS[i], v]; }));
const temSegredos = (loja, s) => loja.segredos.every(n => s[n]);

const TZ = "America/Sao_Paulo";
const hoje = () => new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date());   // 2026-10-21
const esperar = ms => new Promise(r => setTimeout(r, ms));
const STATUS = db.doc("painel/status"), CONFIG = db.doc("painel/config");

async function alerta(loja, msg) {
  await STATUS.set({ alertas: admin.firestore.FieldValue.arrayUnion({ loja, msg: String(msg).slice(0, 200), em: Date.now() }) }, { merge: true });
}
async function limparAlertas(loja) {
  const s = (await STATUS.get()).data() || {};
  const ficam = (s.alertas || []).filter(a => a.loja !== loja && Date.now() - a.em < 3 * 864e5);
  await STATUS.set({ alertas: ficam }, { merge: true });
}

/* ---------- rodada completa ---------- */
async function rodada(origem) {
  const t0 = Date.now();
  const regras = core.regrasDe((await CONFIG.get()).data());
  if (regras.pausado) return { pausado: true };
  const segredos = lerSegredos();

  // 1. o que falta (só nome e quantas casas precisam)
  const snap = await db.collectionGroup("itens").select("nome", "comprado", "excluido", "etapa").get();
  const itens = snap.docs.map(d => ({ ...d.data(), _casa: d.ref.parent.parent.id }));
  const faltam = core.itensQueFaltam(itens, regras.maxItens);

  const bloqueados = new Set((await db.collection("painelBloqueados").get()).docs.map(d => d.id.replace("__", ":")));
  const precosRef = db.collection("precos");
  const atuais = new Map((await db.collection("ofertas").get()).docs.map(d => [d.id, d.data()]));
  const novos = new Map(), lojasOk = {};

  // 2 a 4. busca, filtra e monta o link em cada loja ligada
  for (const loja of LOJAS) {
    if (!regras.lojas[loja.id]) { lojasOk[loja.id] = { ok: false, msg: "Desligada no painel" }; continue; }
    if (loja.soLink) { lojasOk[loja.id] = { ok: true, msg: "Só link, sem preço" }; continue; }
    if (!temSegredos(loja, segredos)) { lojasOk[loja.id] = { ok: false, msg: "Falta conectar a conta de afiliado" }; continue; }
    let erros = 0, ultimoErro = "";
    for (const item of faltam) {
      try {
        const cands = await loja.buscar(segredos, item.nome);
        const hist = new Map();
        for (const c of cands.slice(0, 15)) {
          const k = `${c.loja}__${c.produtoId}`;
          const ref = precosRef.doc(k), d = (await ref.get()).data() || { h: [] };
          const h = (d.h || []).filter(x => x.d !== hoje()).concat([{ d: hoje(), p: c.preco }]).slice(-30);
          await ref.set({ h });
          hist.set(`${c.loja}:${c.produtoId}`, h.map(x => x.p));
        }
        for (const c of core.escolher(cands, item, regras, bloqueados, hist)) {
          const doc = core.docOferta(c, item, Date.now());
          novos.set(core.idOferta(c.loja, item.chave), { ...doc, _casas: item.casas });
        }
      } catch (e) { erros++; ultimoErro = e.message; }
      await esperar(400);                                   // calma com a loja
      if (erros >= 5 && erros > faltam.length / 3) break;   // loja com problema: para só ela
    }
    lojasOk[loja.id] = erros ? { ok: erros < 5, msg: ultimoErro } : { ok: true, msg: "" };
    if (erros >= 5) await alerta(loja.id, `${loja.id}: ${ultimoErro}`); else await limparAlertas(loja.id);
  }

  // 5. publica: troca o que mudou, tira o que não vale mais (de lojas que rodaram bem)
  const lojasRodaram = new Set(Object.entries(lojasOk).filter(([, v]) => v.ok).map(([k]) => k));
  let batch = db.batch(), n = 0, tiradas = 0;
  const flush = async () => { if (n) { await batch.commit(); batch = db.batch(); n = 0; } };
  for (const [id, o] of novos) {
    const { _casas, ...doc } = o;
    batch.set(db.doc(`ofertas/${id}`), doc); n++; if (n >= 400) await flush();
  }
  for (const [id, o] of atuais) {
    if (novos.has(id) || !lojasRodaram.has(o.lojaId)) continue;
    batch.set(db.doc(`painelHist/${id}`), { ...o, motivo: "Acabou o desconto ou o item já foi comprado", tiradaEm: Date.now() });
    batch.delete(db.doc(`ofertas/${id}`)); n += 2; tiradas++; if (n >= 400) await flush();
  }
  await flush();

  // avisos: só as imperdíveis que são novas ou baixaram mais
  const novas = [...novos.entries()].filter(([id, o]) => !atuais.has(id) || (atuais.get(id).off || 0) < o.off).map(([, o]) => o);
  const avisos = await enviarAvisos(novas, regras);

  const r = { em: Date.now(), origem, procurados: faltam.length, novas: novas.length, noAr: novos.size, tiradas, avisos, segundos: Math.round((Date.now() - t0) / 1000) };
  await STATUS.set({ ultimaRodada: r, lojas: lojasOk }, { merge: true });
  await limparHistorico();
  logger.info("rodada", r);
  return r;
}

/* Avisos no celular (FCM). Os aparelhos ficam em casas/{id}/push/{token};
   o app passa a registrar o aparelho quando os avisos com o app fechado forem ligados. */
async function enviarAvisos(novas, regras) {
  const casas = new Set(novas.filter(o => o.imperdivel).flatMap(o => o._casas || []));
  const info = new Map();
  for (const id of casas) { const d = (await db.doc(`casas/${id}`).get()).data() || {}; info.set(id, d.avisoOferta || {}); }
  const fila = core.avisosDoDia(novas, info, regras, hoje());
  let enviados = 0;
  for (const [casaId, ofs] of fila) {
    const toks = (await db.collection(`casas/${casaId}/push`).get()).docs.map(d => d.id);
    if (!toks.length) continue;
    for (const o of ofs) {
      const t = core.textoAviso(o);
      const res = await admin.messaging().sendEachForMulticast({ tokens: toks, notification: t, webpush: { fcmOptions: { link: "/#/achadinhos" } } });
      enviados += res.successCount;
      res.responses.forEach((x, i) => { if (!x.success && /not-registered|invalid/.test(x.error?.code || "")) db.doc(`casas/${casaId}/push/${toks[i]}`).delete(); });
    }
    const ant = info.get(casaId) || {};
    await db.doc(`casas/${casaId}`).set({ avisoOferta: { dia: hoje(), n: (ant.dia === hoje() ? ant.n || 0 : 0) + ofs.length } }, { merge: true });
  }
  return enviados;
}

async function limparHistorico() {
  const velho = Date.now() - 30 * 864e5;
  const s = await db.collection("painelHist").where("tiradaEm", "<", velho).limit(400).get();
  const b = db.batch(); s.docs.forEach(d => b.delete(d.ref)); if (!s.empty) await b.commit();
}

/* ---------- de hora em hora: o link ainda abre? ---------- */
async function checagem() {
  const s = await db.collection("ofertas").get();
  let tiradas = 0;
  for (const d of s.docs) {
    const o = d.data();
    let ok = true;
    try {
      const r = await fetch(o.url, { method: "GET", redirect: "follow", headers: { "User-Agent": "Mozilla/5.0 CozilyBot" }, signal: AbortSignal.timeout(10000) });
      ok = r.status < 400 || r.status === 403 || r.status === 429;   // 403/429: loja bloqueando robô, não é link quebrado
    } catch (e) { ok = true; }                                         // falha de rede não derruba a oferta
    if (Date.now() - (o.atualizadoEm || 0) > 30 * 36e5) ok = false;   // sem atualização há mais de 30 h
    if (!ok) {
      await db.doc(`painelHist/${d.id}`).set({ ...o, motivo: "Link não abre mais ou oferta vencida", tiradaEm: Date.now() });
      await d.ref.delete(); tiradas++;
    } else await d.ref.update({ testadoEm: Date.now() });
    await esperar(300);
  }
  await STATUS.set({ ultimaChecagem: { em: Date.now(), testadas: s.size, tiradas } }, { merge: true });
}

/* ---------- comissões do mês ---------- */
async function comissoes() {
  const segredos = lerSegredos();
  const agora = new Date(), ini = new Date(agora.getFullYear(), agora.getMonth(), 1).getTime();
  const mes = hoje().slice(0, 7), out = { mes, em: Date.now() };
  for (const loja of LOJAS) {
    if (!loja.comissoesDoMes) { out[loja.id] = null; continue; }      // sem relatório automático: ver no site da loja
    if (!temSegredos(loja, segredos)) { out[loja.id] = null; continue; }
    try { out[loja.id] = await loja.comissoesDoMes(segredos, ini, Date.now()); }
    catch (e) { out[loja.id] = null; await alerta(loja.id, `Comissões ${loja.id}: ${e.message}`); }
  }
  await STATUS.set({ comissoes: out }, { merge: true });
}

const opcoes = (extra) => ({ timeZone: TZ, secrets: SEGREDOS, timeoutSeconds: 540, memory: "512MiB", ...extra });
exports.rodadaDiaria = onSchedule(opcoes({ schedule: "0 6 * * *" }), () => rodada("agenda"));
exports.checagemHoraria = onSchedule(opcoes({ schedule: "0 * * * *" }), () => checagem());
exports.comissoesDiarias = onSchedule(opcoes({ schedule: "0 7 * * *" }), () => comissoes());
exports.comandoDoPainel = onDocumentCreated({ document: "painelComandos/{id}", secrets: SEGREDOS, timeoutSeconds: 540, memory: "512MiB" }, async ev => {
  const c = ev.data && ev.data.data(); if (!c) return;
  try {
    if (c.acao === "rodar") await rodada("painel");
    else if (c.acao === "checar") await checagem();
    else if (c.acao === "comissoes") await comissoes();
    await ev.data.ref.update({ feitoEm: Date.now() });
  } catch (e) { await ev.data.ref.update({ erro: String(e.message).slice(0, 200) }); }
});

/* ---------- pagamento (Kiwify) ---------- */
const { onRequest } = require("firebase-functions/v2/https");
const pagamento = require("./pagamento");
const KIWIFY_TOKEN = defineSecret("KIWIFY_TOKEN");
exports.kiwify = onRequest({ secrets: [KIWIFY_TOKEN], cors: false, maxInstances: 2 }, async (req, res) => {
  if (req.method !== "POST") { res.status(405).send("Só POST"); return; }
  const bruto = req.rawBody ? req.rawBody.toString("utf8") : JSON.stringify(req.body || {});
  if (!pagamento.assinaturaOk(bruto, req.query.signature, KIWIFY_TOKEN.value())) { logger.warn("kiwify: assinatura inválida"); res.status(401).send("assinatura"); return; }
  const p = req.body || {}, acao = pagamento.acaoDoPedido(p), email = pagamento.emailDoPedido(p);
  if (!acao || !email) { res.status(200).send("ignorado"); return; }
  try {
    const r = await pagamento.aplicar(db, admin, email, acao, p.order_id);
    logger.info("kiwify", { acao, casas: r.casas.length });
    res.status(200).send("ok");
  } catch (e) { logger.error("kiwify", e); res.status(500).send("erro"); }   // a Kiwify tenta de novo
});
/* Conta nova de quem já tinha pago: libera na hora. */
const functionsV1 = require("firebase-functions/v1");
exports.contaNova = functionsV1.region("southamerica-east1").auth.user().onCreate(async user => {
  const email = (user.email || "").toLowerCase(); if (!email) return;
  const pg = await db.doc(`pagamentos/${email}`).get();
  if (pg.exists && pg.data().pago) await db.doc(`acesso/${user.uid}`).set({ ...pg.data(), em: Date.now() }, { merge: true });
});

exports._interno = { rodada, checagem, comissoes };
