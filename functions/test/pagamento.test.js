const test = require("node:test"), assert = require("node:assert"), crypto = require("crypto");
const p = require("../pagamento");
const corpo = JSON.stringify({ order_id: "1", order_status: "paid", Customer: { email: "Ana@Ex.com " } });
const assina = (c, t) => crypto.createHmac("sha1", t).update(c).digest("hex");
test("assinatura certa passa, errada ou sem token não", () => {
  assert.ok(p.assinaturaOk(corpo, assina(corpo, "tk"), "tk"));
  assert.ok(!p.assinaturaOk(corpo, assina(corpo, "outro"), "tk"));
  assert.ok(!p.assinaturaOk(corpo + " ", assina(corpo, "tk"), "tk"));
  assert.ok(!p.assinaturaOk(corpo, assina(corpo, "tk"), ""));
  assert.ok(!p.assinaturaOk(corpo, undefined, "tk"));
});
test("pago libera, reembolso e chargeback tiram, resto ignora", () => {
  assert.equal(p.acaoDoPedido({ order_status: "paid" }), "liberar");
  assert.equal(p.acaoDoPedido({ webhook_event_type: "order_approved" }), "liberar");
  assert.equal(p.acaoDoPedido({ order_status: "refunded" }), "tirar");
  assert.equal(p.acaoDoPedido({ order_status: "chargedback" }), "tirar");
  assert.equal(p.acaoDoPedido({ order_status: "waiting_payment" }), null);
  assert.equal(p.acaoDoPedido(null), null);
});
test("e-mail normalizado e validado", () => {
  assert.equal(p.emailDoPedido(JSON.parse(corpo)), "ana@ex.com");
  assert.equal(p.emailDoPedido({ Customer: { email: "nada" } }), "");
});
test("libera a casa da pessoa e a casa onde mora junto, nunca o nosso-ap", async () => {
  const docs = {}, db = { doc: k => ({ get: async () => ({ exists: !!docs[k], data: () => docs[k] }), set: async v => { docs[k] = { ...(docs[k] || {}), ...v }; } }) };
  docs["convites/ana@ex.com"] = { casaId: "casaDoLeo" };
  const admin = { auth: () => ({ getUserByEmail: async () => ({ uid: "uidAna" }) }) };
  const r = await p.aplicar(db, admin, "ana@ex.com", "liberar", "1");
  assert.deepEqual(r.casas.sort(), ["casaDoLeo", "uidAna"]);
  assert.equal(docs["acesso/uidAna"].pago, true); assert.equal(docs["pagamentos/ana@ex.com"].pago, true);
  docs["convites/caio@ex.com"] = { casaId: "nosso-ap" };
  const r2 = await p.aplicar(db, { auth: () => ({ getUserByEmail: async () => { throw new Error("x"); } }) }, "caio@ex.com", "liberar", "2");
  assert.deepEqual(r2.casas, []); assert.ok(!docs["acesso/nosso-ap"]);
  await p.aplicar(db, admin, "ana@ex.com", "tirar", "1"); assert.equal(docs["acesso/uidAna"].pago, false);
});
