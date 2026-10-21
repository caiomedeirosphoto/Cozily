/* Shopee: API oficial de afiliados (Shopee Affiliate Open API, Brasil).
   Precisa de dois segredos no Firebase: SHOPEE_APP_ID e SHOPEE_SECRET
   (ficam em Painel de afiliado da Shopee → Open API). O link que volta já tem o seu código. */
const crypto = require("crypto");

const URL = "https://open-api.affiliate.shopee.com.br/graphql";

async function chamar(appId, secret, query, variables) {
  const payload = JSON.stringify({ query, variables });
  const ts = Math.floor(Date.now() / 1000);
  const assinatura = crypto.createHash("sha256").update(appId + ts + payload + secret).digest("hex");
  const r = await fetch(URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `SHA256 Credential=${appId}, Timestamp=${ts}, Signature=${assinatura}` },
    body: payload
  });
  if (!r.ok) throw new Error(`Shopee respondeu ${r.status}`);
  const j = await r.json();
  if (j.errors && j.errors.length) throw new Error("Shopee: " + (j.errors[0].message || "erro"));
  return j.data;
}

const Q_BUSCA = `query($kw:String,$limit:Int){productOfferV2(keyword:$kw,sortType:2,page:1,limit:$limit){nodes{
  itemId productName price priceMin priceMax priceDiscountRate ratingStar sales imageUrl offerLink shopName}}}`;

async function buscar(segredos, termo) {
  const d = await chamar(segredos.SHOPEE_APP_ID, segredos.SHOPEE_SECRET, Q_BUSCA, { kw: termo, limit: 15 });
  const nodes = (d && d.productOfferV2 && d.productOfferV2.nodes) || [];
  return nodes.map(n => {
    const preco = Number(n.priceMin || n.price);
    const taxa = Number(n.priceDiscountRate || 0);           // % de desconto informado pela Shopee
    const precoAntes = taxa > 0 && taxa < 100 ? Math.round(preco / (1 - taxa / 100) * 100) / 100 : 0;
    return {
      loja: "shopee", produtoId: String(n.itemId), nome: n.productName, preco, precoAntes,
      nota: n.ratingStar != null ? Number(n.ratingStar) : null,
      vendidos: n.sales ? `+${n.sales}` : "", img: n.imageUrl || "", url: n.offerLink
    };
  });
}

/* Comissões do mês (relatório de conversões da Shopee). */
const Q_COMISSAO = `query($ini:Int64,$fim:Int64,$cursor:String){conversionReport(purchaseTimeStart:$ini,purchaseTimeEnd:$fim,limit:500,scrollId:$cursor){
  nodes{totalCommission} pageInfo{hasNextPage scrollId}}}`;
async function comissoesDoMes(segredos, ini, fim) {
  let total = 0, cursor = null;
  for (let i = 0; i < 20; i++) {
    const d = await chamar(segredos.SHOPEE_APP_ID, segredos.SHOPEE_SECRET, Q_COMISSAO, { ini: Math.floor(ini / 1000), fim: Math.floor(fim / 1000), cursor });
    const rep = d && d.conversionReport; if (!rep) break;
    for (const n of rep.nodes || []) total += Number(n.totalCommission || 0);
    if (!rep.pageInfo || !rep.pageInfo.hasNextPage) break;
    cursor = rep.pageInfo.scrollId;
  }
  return Math.round(total * 100) / 100;
}

module.exports = { id: "shopee", segredos: ["SHOPEE_APP_ID", "SHOPEE_SECRET"], buscar, comissoesDoMes };
