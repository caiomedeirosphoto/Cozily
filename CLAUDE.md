# Cozily — contexto para continuar o trabalho

Leia isto inteiro antes de mexer em qualquer coisa. Fale sempre em **português do Brasil**, de forma simples (o Caio não é programador).

## O produto
- **Cozily** é um app web instalável (PWA) para montar a casa nova item por item: cômodos, itens com etapas (1 morar, 2 funcional, 3 bonita), caixinha/finanças, lista do mercado, lista de presentes (chá de casa nova) com página pública para convidados, garantias, achadinhos/cupons.
- Dono: **Caio** (caiodanielmedeiros1597@gmail.com). Usa com a noiva **Mirielly**. O apartamento deles fica pronto no fim de 2028. Ele pretende **vender o app** no futuro.
- Endereço atual: https://caiomedeirosphoto.github.io/Cozily/ (GitHub Pages, repo `caiomedeirosphoto/Cozily`). Backend: **Firebase**, projeto `cozily-bae7b` (Auth + Firestore).

## Regras de trabalho (combinadas com o Caio — siga sempre)
- Toda mudança vai para a branch **`dev`**, com a **prévia atualizada**. **Nunca subir para `main` sem o OK explícito dele** (um "pode subir" vale só para aquele pacote).
- **Testar tudo várias vezes** antes de mostrar: claro e escuro, 320 e 390 px, e rodar a bateria inteira de testes. Corrigir coisas fora do lugar.
- Quando ele pedir **storyboard**, fazer o storyboard primeiro.
- Segurança: nunca pedir senha de conta; chaves de afiliado só no servidor; a conta dele mantém os dados e é grátis para sempre; nunca postar com o Instagram pessoal @caiomedeiros.mov.
- A cada versão, aumentar `APP_VERSION` (em index.html, formato `AAAA.MM.DD-N`). O app compara a versão e se atualiza sozinho.
- Regras do Firestore ficam em `firestore.rules`, mas **quem publica é o Caio**, colando no Firebase Console → Firestore → Regras → Publicar. Quando mudar as regras, entregue o texto completo para ele colar e diga a ordem (primeiro subir o app, depois colar). A versão atual do arquivo **já está publicada** por ele.

## Arquitetura (arquivo único)
- Tudo está em **`index.html`**: `<style>` + `<script type="module">`. Seções na ordem: configuração/Firebase e lojas demo (`makeDemoStore`, `makeFirebaseStore`) → helpers/ícones/estado `S` → views (`render`, `viewHome`, `viewRoom`, `viewMercado`, `viewPresentes`...) → sheets (`openSheet`, Ajustes, Quem mora junto, convites, mercado, lista de presentes, toast) → fluxo (login, `handleAuth`, onboarding, ações `data-act`, `start()`).
- **Modo demonstração**: quando `apiKey` é `"COLE_AQUI"`, roda sem Firebase, com dados de exemplo no localStorage (`caio@exemplo.com` / `demonstracao`; `mirielly@exemplo.com` / `demonstracao`). A prévia e os testes usam esse modo.
- `sw.js`: service worker. Busca a página na rede primeiro e usa a cópia guardada sem internet. Também cuida dos avisos.
- Firestore: `casas/{casaId}` (ajustes da casa) com as subcoleções `itens`, `movs`, `compras`, `mercado`, `fotos`; mais `convites/{email}`, `codigos/{code}` (convite por link/WhatsApp, vale 7 dias, uma pessoa), `listas/{slug}` + `reservas`, `erros` (registro de erros, só o Caio lê), `ofertas`, `cupons`. **Toda subcoleção nova precisa de regra própria em `firestore.rules`.**
- A casa do Caio é a legada `nosso-ap` (`LEGACY` no código). As outras contas usam `casas/{uid}`.
- Tema: `data-theme` no `<html>`. O escuro é grafite. Os blocos de CSS escuro são duplicados como `:root:not([data-theme="light"])` e `:root[data-theme="dark"]`.

## Ferramentas (pasta `.dev/`, não vai para o site)
```
cd .dev
bash build.sh        # confere a sintaxe e gera a prévia em .dev/t2/ (cozily.html = artifact; index.html = testes; csp.html)
bash serve.sh        # servidor da prévia em http://localhost:8811 (rode antes dos testes; ele morre entre chamadas)
bash test_all.sh     # roda todos os testes Playwright. Tudo deve sair sem FAIL; no tcrawl só "TOTAL 4" (fontes bloqueadas no sandbox) é esperado
```
- Os testes ficam em `.dev/tests/*.py` (convite, ajustes/conta, fluxo geral, onboarding, verificação de e-mail, dados antigos, CSP, piscada ao voltar, "colocar todos", mercado, arrastar avisos, lista de presentes, varredura de telas). Os prints vão para `.dev/t2/`.
- Para matar o servidor: `for p in $(pgrep -f "[p]ython3 -m http.server 8811"); do kill $p; done` (o colchete evita matar o próprio shell).
- **Prévia (artifact)**: https://claude.ai/artifact/1TzFuaT8bpfbQbS97bW4j6. Para atualizar, leia com Artifact `read` e depois publique `.dev/t2/cozily.html` nesse `url`.
- **Storyboard (Design)**: https://claude.ai/artifact/VVPA2fPgbWL1bZDSeQGT4U
- Liberar para o app: `git checkout main && git pull origin main && git merge --ff-only dev && git push origin main && git checkout dev`.

## Onde paramos (19/10/2026)
Versão **2026.10.19-4 liberada no app** (`main`) em 19/10/2026, com o OK do Caio. **`dev` e `main` estão iguais**. Ela contém as 4 ideias:
1. **Mercado**: ao começar um mês (`novaListaMercado`), o que ficou sem comprar no mês anterior ganha `sobrou: true` e aparece no topo em "Ficou do mês passado" (doc do mês guarda `sobrouDe`). Só marca se usaram a lista (algo foi pro carrinho). Na folha do item (`openMercadoQtd`) aparece o histórico de preço por mês (`historicoPreco`/`variacaoPreco`): "Subiu 15% desde julho", que muda conforme digita o preço.
2. **Item repetido**: no "Anotar", se já existe item com o mesmo nome normalizado (`chaveNome`: sem acento e sem plural), aparece "Já tem Toalhas de banho no Banheiro" com "Abrir o que já tem" / "Anotar mesmo assim".
3. **Início — "Próxima compra"** (`proximaCompra`/`proximaHtml`): item da Etapa 1 com valor previsto, comparado com o disponível da caixinha ("Dá pra comprar…" com botão "Já compramos", ou "Faltam R$ X").
4. **Atividade da casa**: `registrar()` grava em `casas/{id}/atividade` (acao, quem, email, em, alvo, itemId, valor, extra; guarda as 100 últimas) ao anotar, marcar comprado/presente e lançar compra do mercado. Reservas de convidados e quem entrou na casa entram no feed sem gravar. Aparece no Início (3 últimas) e em `#/atividade`. Erros ao gravar não mostram aviso (antes das regras novas, só não grava).
- **Regras novas** em `firestore.rules` (bloco `match /atividade/{id}`): o Caio já colou no Firebase Console (20/10/2026).
- Testes novos: `.dev/tests/tnovas.py` (entrou no `test_all.sh`); prints em `.dev/tests/tprints.py`. A prévia tem histórico de mercado e atividade de exemplo (`demoSamples`).
- Depois de liberar: lembrar o Caio de criar um **convite novo pelo WhatsApp para a Mirielly** (ela abre o link, entra com a conta dela e confirma "Entrar na casa").

## Liberado no app em 20/10/2026: versão 2026.10.20-15 (`dev` e `main` iguais)
- Saudação: quem sai da casa (ou exclui a conta) sai também de `nomes` (`nomesSem`).
- Início novo: anel "Pronto pra morar" (Etapa 1), Próxima compra (com etiqueta de oferta e link "Ver a ordem de compra"), fileira de cômodos (mais atrasados primeiro) com "Ver todos" → `#/comodos` (quadradinhos), cartões Achadinhos + Lista de presentes, Atividade, atalhos Finanças e Mercado. Busca virou ícone no topo.
- Barra de baixo: "Ordem" saiu; entrou **Ofertas** (foguinho) → `#/achadinhos`. Ordem agora é tela aberta pela Próxima compra.
- Ofertas: `ofertaDoItem`/`etqOferta` (foguinho laranja `--orange`) nos itens dos cômodos, na Próxima compra e nos Avisos ("Ofertas do que falta"). Achadinhos: resumo "Dá pra economizar até", maior desconto, seções "Do que falta"/"Outras", dica que fecha (`cozily-x-ach`).
- Item: "Pôr/Tirar da lista de presentes", mostra quem reservou; "Tirar da lista" só texto vermelho.
- Avisos: atividade da casa no lugar de "Outros"; bolinha do sino acende com ações dos outros e reservas.
- Animações: tempos `--t-fast/--t-med/--t-slow` e uma curva; troca de telas com View Transitions (barra de abas parada); filtros com fade (`trocaSuave`). Setinha de voltar presa no alto (topbar sticky, `.float-bar` fixa).
- Mercado em cards por seção (`S.mSec`, `M_CAT_IC`), barra "Ver a lista toda", busca em tudo; Editar junto dos filtros; textos curtos.
- Cards de Achadinhos/Presentes mais baixos; link da lista mostrado como "cozily/<slug>" (copiar manda o endereço completo).
- Próxima compra: um botão só ("Ver a ordem de compra"); sem valor previsto mostra "É o mais importante que falta pra morar".
- Cômodos no Início: mais itens comprados primeiro; empate pela importância (cozinha, quarto, banheiro…).
- Testes novos: `.dev/tests/tinicio.py`. Bateria inteira passou.

## Liberado no app em 21/10/2026: versão 2026.10.21-1 (`dev` e `main` iguais)
- Saudação: nomes com vírgula e "e" só antes do último ("Caio, Mirielly e Ana"); `partesNomes`/`juntaNomes`/`nomesCom`. Textos antigos ("Caio e Mirielly e Ana") aparecem já arrumados.
- Quem entra grava em `chegadas` o nome exato que entrou (`parte`). Ao sair, `nomesSem` tira só esse nome. Casas antigas sem `parte`: tira pelo nome inteiro ou primeiro nome, mas nunca o primeiro da saudação nem o nome de quem fica (antes, uma conta "Caio Medeiros" apagava o "Caio" também).

## Na `dev` (21/10/2026), guardado até ter o domínio: painel de ofertas + robô (app 2026.10.21-2)
- **App**: oferta de 5% a 14% aparece discreta (`etq-of leve`, sem foguinho); 15%+ é "imperdível" (foguinho laranja) e só essas entram nos Avisos. Campo `imperdivel` vem do robô (senão calcula off >= 15).
- **Painel** (`painel/index.html`, vai para `painel.cozily.com.br`; fora do site do GitHub Pages pelo `_config.yml` até ter o domínio): só e-mail e senha, sem criar conta e sem Google. Contas criadas à mão pelo Caio no Firebase. Acesso decidido pelas regras: `painelAdmin()` em `firestore.rules` com os UIDs (hoje `UID_DO_CAIO`/`UID_DA_MIRI` = falta trocar). Telas: Início (comissões, última rodada, alertas, maiores descontos, Rodar agora), Ofertas (no ar / tiradas / bloqueadas, busca, bloquear/liberar), Robô (lojas liga/desliga, regras 5% e 15%, nota mínima, avisos por dia, pausar, sair). Modo demonstração igual ao app (`caio@exemplo.com` / `demonstracao`). Prévia: `.dev/build_painel.py` gera `.dev/t2/painel.html` (testes) e `painel-artifact.html` → artifact https://claude.ai/artifact/Gpzru4Gxh8aG3rwmHSpszv. Teste `.dev/tests/tpainel.py` (no `test_all.sh`).
- **Robô** (`functions/`, Cloud Functions, região southamerica-east1, precisa do Blaze): `rodadaDiaria` 6h, `checagemHoraria`, `comissoesDiarias` 7h, `comandoDoPainel` (doc em `painelComandos`). Regras puras em `functions/core.js` (testes: `cd functions && npm test`). Lojas em `functions/lojas/`: Shopee (Open API de afiliados, segredos SHOPEE_APP_ID/SHOPEE_SECRET, link já vem com comissão, tem relatório de comissões); Mercado Livre (API de busca com ML_CLIENT_ID/ML_CLIENT_SECRET; link de afiliado por modelo ML_LINK_AFILIADO "{url}…", A CONFIRMAR se o programa permite; sem relatório); Amazon só link até liberar a PA-API. Coleções: `painel/config`, `painel/status`, `painelHist` (30 dias), `painelBloqueados/{loja}__{produtoId}`, `painelComandos`, `precos` (30 dias por produto). Avisos FCM para `casas/{id}/push/{token}` (o app ainda NÃO registra aparelho: fazer junto com a mudança de domínio, com regra própria) e contador `avisoOferta` na casa.
- **Ordem para ligar**: domínio → Firebase Hosting (app + painel) → Blaze → segredos (`firebase functions:secrets:set`) → deploy das functions → Caio cria as 2 contas e passa os UIDs → regras novas coladas → repositório privado.

## Liberado no app em 23/10/2026: teste grátis de 7 dias (app 2026.10.23-1, `dev` e `main` iguais; inclui o 2026.10.21-2)
- Conta nova grava `testes/{uid}` {em} uma vez (regra: só criar, hora de agora ±10 min; nunca muda/apaga). `acessoInfo()`: gratis (nosso-ap) / pago (`acesso/{casaId}.pago`, só servidor grava) / teste (dias) / acabou. Quem mora junto segue o status da casa.
- Acabou = só ver: cliques de mudança (`SO_COM_ACESSO`) e o form do mercado abrem `openPlano()`; `write()` com permission-denied também. Regras: `liberada(casaId)` em create/update de itens, movs, compras, mercado, atividade, fotos (ler e apagar continuam).
- Preço: R$ 39,90 promocional (-20% de R$ 49,90) SÓ enquanto o teste vale (prazo real = fim do teste); depois R$ 49,90. Constantes `PRECO_CHEIO`, `PRECO_PROMO`, `KIWIFY_PROMO` (link com preço promo), `KIWIFY_CHECKOUT` (cheio) — vazios até a venda abrir ("Pagamento abre em breve"). Link leva `?email=&name=`.
- Início: barra "Teste grátis · faltam N dias · 20% off até o teste acabar · R$ 39,90"; fim: cartão rosa "Seu teste grátis acabou". Ajustes → Plano. Prévia tem "Simular fim do teste/pagamento".
- Servidor (`functions/`, Blaze): `kiwify` (webhook, assinatura HMAC-SHA1 com segredo KIWIFY_TOKEN; pago libera, reembolso/chargeback tira; libera `acesso/{uid}` e a casa do convite; guarda `pagamentos/{email}`) e `contaNova` (quem pagou antes de criar conta). Testes: `functions/test/pagamento.test.js`, `.dev/tests/tteste.py`.
- Regras novas (testes/acesso/pagamentos + liberada + painel) entregues ao Caio em 23/10 pra colar.

## Liberado no app em 23/10/2026: versão 2026.10.23-3 (`dev` e `main` iguais)
- Pente fino: tokens `--muted2`/`--faint` mais legíveis (claro e escuro), alvos de toque maiores ("editar" orçamento, "Ver todas", "Onde comprar"), lista de presentes em 320 px (`.g-th` menor), `.offer .off` sem quebrar. Teste de varredura `.dev/tests/taudit.py` (todas as telas e folhas; prints em `.dev/t4/audit`).
- `barraTopo()`: a cor da barra do celular (meta theme-color) escurece junto com as folhas e volta ao fechar (antes piscava uma faixa escura no iPhone).

## PRÓXIMA TAREFA
Esperar o domínio cozily.com.br. Antes: Regras da atividade já coladas pelo Caio (20/10). A Mirielly já entrou na casa.

## Pendências e riscos conhecidos
- **Domínio cozily.com.br** (ele vai comprar): migrar para o Firebase Hosting com cabeçalhos de segurança; página no github.io que redireciona mantendo o `#`; `authDomain` no próprio domínio. Isso resolve o **login com Google no iPhone com o app instalado** (hoje pode falhar por bloqueio de armazenamento entre domínios) e os **e-mails caindo no spam** (remetente do próprio domínio). Depois: App Check e restringir a chave da API ao domínio.
- **Avisos com o app fechado** e **backup automático** precisam do plano Blaze (Cloud Functions/Scheduler). Fotos hoje ficam em base64 no Firestore (limite ~900 KB), e o ideal futuro é o Cloud Storage (também Blaze).
- **Achadinhos/cupons** só aparecem quando existem documentos em `ofertas`/`cupons` (hoje vazios). Falta um painel de admin para cadastrar, e os códigos de afiliado (`AFILIADO` vazio). O Caio ainda não respondeu se quer seguir.
- Aviso do Firebase sobre o fim do Dynamic Links **não afeta** o app (é web).
- Logo oficial: o "C encorpada" (casinha em forma de C com ponto bege). Imagens de apresentação foram feitas no estilo "aquon".
