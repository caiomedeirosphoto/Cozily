/* Mercado Livre: busca pela API oficial (precisa de um app criado em developers.mercadolivre.com.br).
   Segredos: ML_CLIENT_ID e ML_CLIENT_SECRET.
   Link de afiliado: o Mercado Livre não tem (até onde sabemos) um jeito oficial de gerar o link por robô.
   Por isso o link é montado a partir do produto com o seu código (segredo ML_LINK_AFILIADO, um modelo
   tipo "{url}?matt_tool=SEUCODIGO" copiado do gerador de links do programa de afiliados).
   Sem esse segredo o robô NÃO publica ofertas do Mercado Livre (não adianta mandar link sem comissão). */

let token = null, tokenAte = 0;
async function pegarToken(s) {
  if (token && Date.now() < tokenAte) return token;
  const r = await fetch("https://api.mercadolibre.com/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body: new URLSearchParams({ grant_type: "client_credentials", client_id: s.ML_CLIENT_ID, client_secret: s.ML_CLIENT_SECRET })
  });
  if (!r.ok) throw new Error(`Mercado Livre (login) respondeu ${r.status}`);
  const j = await r.json();
  token = j.access_token; tokenAte = Date.now() + Math.max(60, (j.expires_in || 3600) - 120) * 1000;
  return token;
}

function linkAfiliado(modelo, url) {
  if (!modelo || !modelo.includes("{url}")) return "";
  return modelo.replace("{url}", url);
}

async function buscar(s, termo) {
  if (!linkAfiliado(s.ML_LINK_AFILIADO, "x")) throw new Error("Falta o modelo do link de afiliado do Mercado Livre");
  const tk = await pegarToken(s);
  const r = await fetch(`https://api.mercadolibre.com/sites/MLB/search?q=${encodeURIComponent(termo)}&limit=15&condition=new`, { headers: { Authorization: `Bearer ${tk}` } });
  if (!r.ok) throw new Error(`Mercado Livre respondeu ${r.status}`);
  const j = await r.json();
  return (j.results || []).map(p => ({
    loja: "mercadolivre", produtoId: String(p.id), nome: p.title,
    preco: Number(p.price), precoAntes: Number(p.original_price || 0),
    nota: null, vendidos: "",
    img: (p.thumbnail || "").replace(/^http:/, "https:"),
    url: linkAfiliado(s.ML_LINK_AFILIADO, p.permalink)
  }));
}

module.exports = { id: "mercadolivre", segredos: ["ML_CLIENT_ID", "ML_CLIENT_SECRET", "ML_LINK_AFILIADO"], buscar, comissoesDoMes: null };
