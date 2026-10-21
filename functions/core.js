/* Regras do robô de ofertas, sem nada de internet ou banco (dá pra testar sozinho).
   Tudo o que decide "essa oferta entra ou não" está aqui. */

const slug = s => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
  .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "x";

const REGRAS_PADRAO = Object.freeze({
  descontoMin: 5,        // a partir daqui a oferta aparece no item
  imperdivelMin: 15,     // a partir daqui ganha destaque e aviso no celular
  notaMin: 4.5,          // nota mínima do produto (quando a loja informa)
  avisosPorDia: 1,       // avisos de oferta por casa, por dia
  maxItens: 150,         // quantos itens diferentes procurar por rodada
  lojas: { shopee: true, mercadolivre: true, amazon: true }
});

function regrasDe(cfg) {
  const r = { ...REGRAS_PADRAO, ...(cfg || {}) };
  r.lojas = { ...REGRAS_PADRAO.lojas, ...((cfg || {}).lojas || {}) };
  const num = (v, min, max, pad) => (typeof v === "number" && isFinite(v) ? Math.min(max, Math.max(min, v)) : pad);
  r.descontoMin = num(r.descontoMin, 0, 90, REGRAS_PADRAO.descontoMin);
  r.imperdivelMin = Math.max(r.descontoMin, num(r.imperdivelMin, 0, 95, REGRAS_PADRAO.imperdivelMin));
  r.notaMin = num(r.notaMin, 0, 5, REGRAS_PADRAO.notaMin);
  r.avisosPorDia = Math.round(num(r.avisosPorDia, 0, 5, REGRAS_PADRAO.avisosPorDia));
  r.maxItens = Math.round(num(r.maxItens, 10, 500, REGRAS_PADRAO.maxItens));
  return r;
}

/* Itens que faltam em todas as casas: só o nome (sem dado de ninguém), com quantas casas precisam dele. */
function itensQueFaltam(itens, max) {
  const m = new Map();
  for (const it of itens) {
    if (!it || !it.nome || it.excluido) continue;
    if (it.comprado) continue;          // já compraram (ou ganharam)
    const k = slug(it.nome);
    const cur = m.get(k) || { chave: k, nome: String(it.nome).trim().slice(0, 80), casas: new Set(), etapa: it.etapa || 3 };
    if (it._casa) cur.casas.add(it._casa);
    cur.etapa = Math.min(cur.etapa, it.etapa || 3);
    m.set(k, cur);
  }
  return [...m.values()]
    .map(x => ({ ...x, casas: [...x.casas] }))
    .sort((a, b) => (b.casas.length - a.casas.length) || (a.etapa - b.etapa) || a.nome.localeCompare(b.nome))
    .slice(0, max);
}

const descontoDe = o => (o && o.preco > 0 && o.precoAntes > o.preco ? Math.round((1 - o.preco / o.precoAntes) * 100) : 0);

/* Desconto "de verdade": se o preço "de" for maior que o maior preço visto nos últimos 30 dias,
   usa o maior preço visto (evita o truque de subir o preço antes da promoção). */
function precoAntesReal(o, historico) {
  const h = (historico || []).filter(p => p > 0);
  if (h.length < 7) return o.precoAntes;            // pouco histórico: confia na loja
  const maior = Math.max(...h);
  return Math.min(o.precoAntes || 0, maior);
}

/* Escolhe a melhor oferta de cada loja para um item, seguindo as regras. */
function escolher(candidatos, item, regras, bloqueados, historicos) {
  const ok = [];
  for (const c of candidatos) {
    if (!c || !c.url || !(c.preco > 0)) continue;
    const key = c.loja + ":" + c.produtoId;
    if (bloqueados && bloqueados.has(key)) continue;
    if (c.nota != null && c.nota < regras.notaMin) continue;
    if (!pareceOItem(c.nome, item.nome)) continue;
    const antes = precoAntesReal(c, historicos && historicos.get(key));
    const off = descontoDe({ preco: c.preco, precoAntes: antes });
    if (off < regras.descontoMin) continue;
    ok.push({ ...c, precoAntes: antes, off });
  }
  const porLoja = new Map();
  for (const c of ok) {
    const cur = porLoja.get(c.loja);
    if (!cur || c.preco < cur.preco || (c.preco === cur.preco && c.off > cur.off)) porLoja.set(c.loja, c);
  }
  return [...porLoja.values()].map(c => ({ ...c, imperdivel: c.off >= regras.imperdivelMin }));
}

/* O título do produto precisa ter as palavras principais do item ("Air fryer" -> "air" e "fryer"). */
const PARADAS = new Set(["de", "da", "do", "das", "dos", "e", "com", "para", "pra", "a", "o", "em", "kit", "jogo", "conjunto"]);
function pareceOItem(titulo, item) {
  const ts = slug(titulo).split("-");
  const ps = slug(item).split("-").filter(p => p.length > 1 && !PARADAS.has(p));
  if (!ps.length) return true;
  /* compara pelo começo da palavra, pra plural e singular baterem (lençóis / lençol, toalhas / toalha) */
  const raiz = p => p.length <= 4 ? p : p.slice(0, Math.max(4, p.length - 2));
  return ps.every(p => ts.some(t => t.startsWith(raiz(p)) || (t.length >= 4 && p.startsWith(raiz(t)))));
}

/* Documento que o app lê em ofertas/{id}. O app só usa estes campos. */
function docOferta(c, item, agora) {
  return {
    nome: String(c.nome).slice(0, 140),
    para: item.nome,
    etapa: item.etapa || 3,
    preco: c.preco,
    precoAntes: c.precoAntes,
    off: c.off,
    imperdivel: !!c.imperdivel,
    loja: { shopee: "Shopee", mercadolivre: "Mercado Livre", amazon: "Amazon" }[c.loja] || c.loja,
    lojaId: c.loja,
    produtoId: String(c.produtoId),
    url: c.url,
    img: c.img || "",
    nota: c.nota != null ? c.nota : null,
    vendidos: c.vendidos || "",
    listas: item.casas ? item.casas.length : 0,
    atualizadoEm: agora,
    testadoEm: agora
  };
}
const idOferta = (lojaId, chaveItem) => `${lojaId}--${chaveItem}`.slice(0, 200);

/* Quais casas recebem aviso hoje: só oferta imperdível, item que a casa precisa, e respeitando o limite por dia. */
function avisosDoDia(novas, casasInfo, regras, hoje) {
  const out = new Map();
  if (!regras.avisosPorDia) return out;
  const imperdiveis = novas.filter(o => o.imperdivel).sort((a, b) => b.off - a.off);
  for (const o of imperdiveis) {
    for (const casaId of o._casas || []) {
      const info = casasInfo.get(casaId) || { dia: "", n: 0 };
      const ja = info.dia === hoje ? info.n : 0;
      const fila = out.get(casaId) || [];
      if (ja + fila.length >= regras.avisosPorDia) continue;
      fila.push(o); out.set(casaId, fila);
    }
  }
  return out;
}

const textoAviso = o => ({
  title: "Oferta imperdível no Cozily",
  body: `${o.para} da sua lista está ${o.off}% mais barato na ${o.loja}`
});

module.exports = { slug, REGRAS_PADRAO, regrasDe, itensQueFaltam, descontoDe, precoAntesReal, escolher, pareceOItem, docOferta, idOferta, avisosDoDia, textoAviso };
