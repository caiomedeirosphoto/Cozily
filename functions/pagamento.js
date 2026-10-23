/* Pagamento pela Cakto: libera (ou tira) o acesso da casa sozinho.
   - A Cakto chama o endereço da function "cakto" a cada venda aprovada, reembolso ou chargeback.
   - O aviso traz a chave secreta do webhook (segredo CAKTO_SECRET). Sem a chave certa, nada acontece,
     então ninguém consegue fingir uma compra.
   - Cada compra vale 1 ano. Comprar de novo antes de vencer soma mais 1 ano a partir do fim atual.
   - Libera a casa da própria pessoa (casas/{uid}) e a casa em que ela mora junto (convite), se tiver.
   - Se a pessoa pagou antes de criar a conta, o pagamento fica guardado e é liberado quando a conta nascer.
   A Cakto pode mudar nomes de campo; por isso as leituras abaixo aceitam as variações conhecidas. */
const crypto = require("crypto");

const ANO_MS = 365 * 864e5;

/* Regras puras (testadas em test/pagamento.test.js). */

/* Chave secreta do webhook: vem no corpo ("secret") ou num cabeçalho. Comparação em tempo constante. */
function chaveDoAviso(corpo, cabecalhos) {
  const h = cabecalhos || {};
  return String((corpo && (corpo.secret || corpo.token)) || h["x-cakto-secret"] || h["x-webhook-secret"] || h["authorization"] || "")
    .replace(/^Bearer\s+/i, "").trim();
}
function chaveOk(recebida, segredo) {
  if (!segredo || !recebida) return false;
  const a = crypto.createHash("sha256").update(String(recebida)).digest();
  const b = crypto.createHash("sha256").update(String(segredo)).digest();
  return crypto.timingSafeEqual(a, b);
}

const dadosDe = p => (p && typeof p.data === "object" && p.data) || p || {};

/* O que fazer com o aviso: "liberar", "tirar" ou null (ignorar). */
function acaoDoPedido(p) {
  if (!p || typeof p !== "object") return null;
  const d = dadosDe(p);
  const evento = String(p.event || p.event_type || p.type || "").toLowerCase();
  const status = String(d.status || p.status || "").toLowerCase();
  if (["purchase_refused", "refused"].includes(evento)) return null;
  if (["refund", "refunded", "purchase_refunded", "chargeback", "purchase_chargeback"].includes(evento)) return "tirar";
  if (["refunded", "chargeback", "chargedback"].includes(status)) return "tirar";
  if (["purchase_approved", "approved", "paid"].includes(evento)) return "liberar";
  if (!evento && ["paid", "approved"].includes(status)) return "liberar";
  return null;
}
function emailDoPedido(p) {
  const d = dadosDe(p);
  const c = d.customer || d.Customer || d.buyer || {};
  const e = String(c.email || d.email || "").trim().toLowerCase();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) ? e : "";
}
function idDoPedido(p) {
  const d = dadosDe(p);
  return String(d.id || d.refId || d.order_id || p.id || "");
}

/* Até quando vale: 1 ano a partir de agora, ou a partir do fim atual se ainda estiver valendo. */
function novoPrazo(ateAtual, agora) {
  const base = ateAtual && ateAtual > agora ? ateAtual : agora;
  return base + ANO_MS;
}

/* Casas que o pagamento libera. */
async function casasDaPessoa(db, admin, email) {
  const casas = new Set();
  let uid = null;
  try { uid = (await admin.auth().getUserByEmail(email)).uid; } catch (e) { uid = null; }
  if (uid) casas.add(uid);
  const conv = await db.doc(`convites/${email}`).get();
  if (conv.exists && conv.data().casaId) casas.add(conv.data().casaId);
  casas.delete("nosso-ap");                       // essa já é grátis pra sempre
  return { uid, casas: [...casas] };
}

async function aplicar(db, admin, email, acao, pedido, agora = Date.now()) {
  const { uid, casas } = await casasDaPessoa(db, admin, email);
  const pago = acao === "liberar";
  const ref = db.doc(`pagamentos/${email}`);
  const antes = await ref.get();
  const ant = antes.exists ? antes.data() : {};
  const pedidoTxt = String(pedido || "");
  /* o mesmo aviso chegando duas vezes não soma outro ano */
  const repetido = pago && pedidoTxt && ant.pago && ant.pedido === pedidoTxt;
  const ate = pago ? (repetido ? ant.ate : novoPrazo(ant.pago ? ant.ate : 0, agora)) : (ant.ate || agora);
  const info = { pago, ate, email, pedido: pedidoTxt, em: agora };
  await ref.set(info, { merge: true });          // fica guardado (serve pra quem ainda não tem conta)
  for (const c of casas) await db.doc(`acesso/${c}`).set(info, { merge: true });
  return { uid, casas, pago, ate };
}

module.exports = { chaveDoAviso, chaveOk, acaoDoPedido, emailDoPedido, idDoPedido, novoPrazo, casasDaPessoa, aplicar, ANO_MS };
