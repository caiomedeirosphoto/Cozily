const test = require("node:test"), assert = require("node:assert");
const p = require("../pagamento");
const aprovado = { secret: "tk", event: "purchase_approved", data: { id: "A1", status: "paid", customer: { email: "Ana@Ex.com " } } };
test("chave certa passa, errada ou vazia não", () => {
  assert.ok(p.chaveOk(p.chaveDoAviso(aprovado, {}), "tk"));
  assert.ok(!p.chaveOk(p.chaveDoAviso({ ...aprovado, secret: "outra" }, {}), "tk"));
  assert.ok(!p.chaveOk(p.chaveDoAviso({ event: "purchase_approved" }, {}), "tk"));
  assert.ok(!p.chaveOk("tk", ""));
  assert.ok(p.chaveOk(p.chaveDoAviso({}, { "x-cakto-secret": "tk" }), "tk"));
});
test("aprovado libera, reembolso e chargeback tiram, resto ignora", () => {
  assert.equal(p.acaoDoPedido(aprovado), "liberar");
  assert.equal(p.acaoDoPedido({ event: "refund", data: {} }), "tirar");
  assert.equal(p.acaoDoPedido({ event: "chargeback", data: {} }), "tirar");
  assert.equal(p.acaoDoPedido({ event: "purchase_refused", data: { status: "refused" } }), null);
  assert.equal(p.acaoDoPedido({ event: "pix_gerado", data: { status: "waiting_payment" } }), null);
  assert.equal(p.acaoDoPedido({ event: "checkout_abandonment", data: {} }), null);
  assert.equal(p.acaoDoPedido(null), null);
});
test("e-mail normalizado e validado; id do pedido", () => {
  assert.equal(p.emailDoPedido(aprovado), "ana@ex.com");
  assert.equal(p.emailDoPedido({ data: { customer: { email: "nada" } } }), "");
  assert.equal(p.idDoPedido(aprovado), "A1");
});
test("prazo: 1 ano; renovar antes de vencer soma a partir do fim", () => {
  const agora = 1e12;
  assert.equal(p.novoPrazo(0, agora), agora + p.ANO_MS);
  assert.equal(p.novoPrazo(agora + 10, agora), agora + 10 + p.ANO_MS);
  assert.equal(p.novoPrazo(agora - 10, agora), agora + p.ANO_MS);
});
test("libera a casa da pessoa e a casa onde mora junto, nunca o nosso-ap; aviso repetido não soma", async () => {
  const docs = {}, db = { doc: k => ({ get: async () => ({ exists: !!docs[k], data: () => docs[k] }), set: async v => { docs[k] = { ...(docs[k] || {}), ...v }; } }) };
  docs["convites/ana@ex.com"] = { casaId: "casaDoLeo" };
  const admin = { auth: () => ({ getUserByEmail: async () => ({ uid: "uidAna" }) }) };
  const agora = 1e12;
  const r = await p.aplicar(db, admin, "ana@ex.com", "liberar", "A1", agora);
  assert.deepEqual(r.casas.sort(), ["casaDoLeo", "uidAna"]);
  assert.equal(docs["acesso/uidAna"].pago, true); assert.equal(docs["acesso/uidAna"].ate, agora + p.ANO_MS);
  await p.aplicar(db, admin, "ana@ex.com", "liberar", "A1", agora + 5);
  assert.equal(docs["acesso/uidAna"].ate, agora + p.ANO_MS);
  await p.aplicar(db, admin, "ana@ex.com", "liberar", "A2", agora + 5);
  assert.equal(docs["acesso/uidAna"].ate, agora + 2 * p.ANO_MS);
  docs["convites/caio@ex.com"] = { casaId: "nosso-ap" };
  const r2 = await p.aplicar(db, { auth: () => ({ getUserByEmail: async () => { throw new Error("x"); } }) }, "caio@ex.com", "liberar", "2", agora);
  assert.deepEqual(r2.casas, []); assert.ok(!docs["acesso/nosso-ap"]);
  await p.aplicar(db, admin, "ana@ex.com", "tirar", "A2", agora); assert.equal(docs["acesso/uidAna"].pago, false);
});
