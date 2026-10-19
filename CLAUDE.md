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
Versão **2026.10.19-3 liberada no app** (`main`) em 19/10/2026, com o OK do Caio. Ela contém:
1. **Convite pelo WhatsApp corrigido.** Causa: o código do convite era salvo no mesmo toque que abria o WhatsApp, e o iPhone pausava o app antes de salvar. Agora o fluxo é "Criar convite pro WhatsApp", que espera o servidor confirmar, e só então aparecem "Mandar no WhatsApp" e "Copiar convite". Se o link falhar, a pessoa vê "Não achamos esse convite", com "Tentar de novo", em vez de cair numa casa nova. Quem tenta criar conta com um e-mail que já existe é levado para "Entrar", com orientação (Google ou "Esqueci minha senha").
2. **Mercado**: busca na lista; preço por item (kg/g/L = valor da prateleira do pacote; un/pct/cx/dz = preço de cada × quantidade) com total da linha; estimativa da lista e valor do carrinho; "Lançar compra" já preenchido com o total do carrinho; o app lembra o último preço do item.
3. **Avisos (toasts) arrastáveis** para dispensar: para os lados, ou para a borda.
4. **App abre sem internet** (service worker com rede primeiro), com o aviso "Sem internet · salva quando o sinal voltar". Login protegido contra corrida dupla. "Tirar a lista do ar" agora apaga também as reservas.
5. Ferramentas de build e teste levadas para `.dev/`, e este arquivo.

Já está no app principal (versões anteriores): convite por e-mail com senha; nome e relação de quem é convidado; tela de boas-vindas; tirar pessoas da casa; excluir conta; política de privacidade (contato: e-mail do Caio); registro de erros (Ajustes › Sua conta › Erros do app, só ele vê); Ajustes organizados; "Colocar todos" na lista de presentes; confirmação de e-mail; regras mais rígidas.

## PRÓXIMA TAREFA
Implementar estas 4 ideias na `dev`, testar bem e **mandar um print de cada tela nova** (SendUserFile), depois perguntar se pode subir:
1. **Mercado — virada do mês e histórico de preço**: ao começar o mês seguinte (`novaListaMercado`), o que ficou sem comprar aparece no topo, numa seção "Ficou do mês passado". Na folha do item (`openMercadoQtd`), mostrar o histórico de preço ("subiu 12% desde agosto"), usando os preços dos meses anteriores.
2. **Item repetido**: ao anotar um item que já existe (mesmo nome normalizado, em outro cômodo ou no mesmo), avisar "Já tem Toalha de banho no Banheiro" com opção de abrir o existente ou anotar mesmo assim.
3. **Início — "Próxima compra"**: card com o item mais importante que falta (Etapa 1, com valor previsto), comparando com o que tem na caixinha ("dá pra comprar com o que já guardaram" / "faltam R$ X").
4. **Atividade da casa**: feed "Mirielly marcou Geladeira como comprada", "Caio anotou Cortina". Gravar quem fez (email/nome) e quando, nas ações principais (marcar comprado, anotar, presente reservado, compra do mercado lançada). Sugestão: subcoleção `casas/{id}/atividade` (limite ~100 últimas). **Precisa de regra nova** no `firestore.rules` (`match /atividade/{id} { allow read, write: if isMember(casaId); }`), e o Caio precisa colar as regras depois de liberar.
Depois de liberar: lembrar o Caio de criar um **convite novo pelo WhatsApp para a Mirielly**. Ela abre o link, entra com a conta dela e confirma "Entrar na casa". A casa vazia que ela criou sem querer fica de lado.

## Pendências e riscos conhecidos
- **Domínio cozily.com.br** (ele vai comprar): migrar para o Firebase Hosting com cabeçalhos de segurança; página no github.io que redireciona mantendo o `#`; `authDomain` no próprio domínio. Isso resolve o **login com Google no iPhone com o app instalado** (hoje pode falhar por bloqueio de armazenamento entre domínios) e os **e-mails caindo no spam** (remetente do próprio domínio). Depois: App Check e restringir a chave da API ao domínio.
- **Avisos com o app fechado** e **backup automático** precisam do plano Blaze (Cloud Functions/Scheduler). Fotos hoje ficam em base64 no Firestore (limite ~900 KB), e o ideal futuro é o Cloud Storage (também Blaze).
- **Achadinhos/cupons** só aparecem quando existem documentos em `ofertas`/`cupons` (hoje vazios). Falta um painel de admin para cadastrar, e os códigos de afiliado (`AFILIADO` vazio). O Caio ainda não respondeu se quer seguir.
- Aviso do Firebase sobre o fim do Dynamic Links **não afeta** o app (é web).
- Logo oficial: o "C encorpada" (casinha em forma de C com ponto bege). Imagens de apresentação foram feitas no estilo "aquon".
