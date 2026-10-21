const test = require("node:test"), assert = require("node:assert");
const c = require("../core");
const R = c.regrasDe({});
const item = { chave: "air-fryer", nome: "Air fryer", etapa: 2, casas: ["a", "b"] };
const cand = (o) => ({ loja: "shopee", produtoId: "1", nome: "Fritadeira Air Fryer 4L", preco: 300, precoAntes: 330, nota: 4.8, url: "https://x", ...o });

test("regras padrão: 5% aparece, 15% imperdível", () => { assert.equal(R.descontoMin, 5); assert.equal(R.imperdivelMin, 15); });
test("imperdível nunca abaixo do mínimo", () => { assert.equal(c.regrasDe({ descontoMin: 20, imperdivelMin: 10 }).imperdivelMin, 20); });
test("4% não entra, 9% entra discreto, 20% imperdível", () => {
  assert.equal(c.escolher([cand({ precoAntes: 312.5 })], item, R).length, 0);
  const a = c.escolher([cand()], item, R); assert.equal(a.length, 1); assert.equal(a[0].off, 9); assert.equal(a[0].imperdivel, false);
  const b = c.escolher([cand({ precoAntes: 375 })], item, R); assert.equal(b[0].imperdivel, true);
});
test("nota baixa, sem link e produto errado ficam de fora", () => {
  assert.equal(c.escolher([cand({ nota: 4.0 })], item, R).length, 0);
  assert.equal(c.escolher([cand({ url: "" })], item, R).length, 0);
  assert.equal(c.escolher([cand({ nome: "Capa para celular" })], item, R).length, 0);
});
test("bloqueado não entra", () => { assert.equal(c.escolher([cand()], item, R, new Set(["shopee:1"])).length, 0); });
test("uma oferta por loja, a mais barata", () => {
  const l = c.escolher([cand(), cand({ produtoId: "2", preco: 280, precoAntes: 330 }), cand({ loja: "mercadolivre", produtoId: "9" })], item, R);
  assert.equal(l.length, 2); assert.equal(l.find(x => x.loja === "shopee").produtoId, "2");
});
test("preço 'de' inflado usa o maior preço dos últimos 30 dias", () => {
  const hist = new Map([["shopee:1", [300, 305, 310, 300, 302, 301, 300]]]);
  assert.equal(c.escolher([cand({ precoAntes: 400 })], item, R, null, hist).length, 0);   // 300 vs 310 = 3%
});
test("itens que faltam: ignora comprado e excluído, junta casas, mais pedidos primeiro", () => {
  const l = c.itensQueFaltam([
    { nome: "Geladeira", _casa: "a", etapa: 1 }, { nome: "geladeira", _casa: "b", etapa: 1 },
    { nome: "Air fryer", _casa: "a", etapa: 2 }, { nome: "Sofá", _casa: "a", comprado: true }, { nome: "Mesa", _casa: "a", excluido: true }], 10);
  assert.deepEqual(l.map(x => x.nome), ["Geladeira", "Air fryer"]); assert.equal(l[0].casas.length, 2);
});
test("avisos: só imperdível e no máximo 1 por casa por dia", () => {
  const o1 = { off: 30, imperdivel: true, _casas: ["a", "b"] }, o2 = { off: 20, imperdivel: true, _casas: ["a"] }, o3 = { off: 9, imperdivel: false, _casas: ["c"] };
  const f = c.avisosDoDia([o2, o1, o3], new Map([["b", { dia: "2026-10-21", n: 1 }]]), R, "2026-10-21");
  assert.equal(f.get("a").length, 1); assert.equal(f.get("a")[0], o1); assert.ok(!f.has("b")); assert.ok(!f.has("c"));
});
test("plural no nome do item", () => { assert.ok(c.pareceOItem("Kit 4 Toalhas de Banho Algodão", "Toalhas de banho")); assert.ok(c.pareceOItem("Lençol com elástico casal", "Lençóis com elástico")); });
