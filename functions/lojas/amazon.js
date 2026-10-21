/* Amazon: por enquanto só link (sem preço).
   A Amazon só deixa mostrar preço que venha da ferramenta oficial dela (Product Advertising API),
   e essa ferramenta só é liberada depois que a conta de afiliado já fez vendas.
   Até lá o robô não publica ofertas da Amazon; os botões "Amazon" do app levam à busca com o seu código.
   Quando a ferramenta for liberada, é aqui que entra a busca com preço. */
async function buscar() { return []; }
module.exports = { id: "amazon", segredos: [], buscar, comissoesDoMes: null, soLink: true };
