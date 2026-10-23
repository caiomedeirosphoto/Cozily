/* Pagamento pela Kiwify: libera (ou tira) o acesso da casa sozinho.
   - A Kiwify chama o endereço da function "kiwify" a cada venda, reembolso ou chargeback.
   - O pedido vem assinado com o token do webhook (segredo KIWIFY_TOKEN), então ninguém consegue fingir uma compra.
   - Libera a casa da própria pessoa (casas/{uid}) e a casa em que ela mora junto (convite), se tiver.
   - Se a pessoa pagou antes de criar a conta, o pagamento fica guardado e é liberado quando a conta nascer. */
const crypto = require("crypto");

/* Regras puras (testadas em test/pagamento.test.js). */
function assinaturaOk(corpoBruto, assinatura, token) {
  if (!token || !assinatura || !corpoBruto) return false;
  const esperado = crypto.createHmac("sha1", token).update(corpoBruto).digest("hex");
  const a = Buffer.from(String(assinatura)), b = Buffer.from(esperado);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

/* O que fazer com o aviso da Kiwify: "liberar", "tirar" ou null (ignorar). */
function acaoDoPedido(p) {
  if (!p || typeof p !== "object") return null;
  const status = String(p.order_status || "").toLowerCase();
  const evento = String(p.webhook_event_type || "").toLowerCase();
  if (status === "paid" || evento === "order_approved") return "liberar";
  if (["refunded", "chargedback", "chargeback"].includes(status) || ["order_refunded", "chargeback"].includes(evento)) return "tirar";
  return null;
}
function emailDoPedido(p) {
  const c = (p && (p.Customer || p.customer)) || {};
  const e = String(c.email || "").trim().toLowerCase();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) ? e : "";
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

async function aplicar(db, admin, email, acao, pedido) {
  const { uid, casas } = await casasDaPessoa(db, admin, email);
  const pago = acao === "liberar";
  const info = { pago, email, pedido: String(pedido || ""), em: Date.now() };
  await db.doc(`pagamentos/${email}`).set(info, { merge: true });   // fica guardado (serve pra quem ainda não tem conta)
  for (const c of casas) await db.doc(`acesso/${c}`).set(info, { merge: true });
  return { uid, casas, pago };
}

module.exports = { assinaturaOk, acaoDoPedido, emailDoPedido, casasDaPessoa, aplicar };
