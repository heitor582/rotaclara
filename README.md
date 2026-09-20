# RotaClara

MVP acadêmico de monitoramento de tempo parado em roteiros de entrega. Engenharia de Software II, Trabalho 2.

## Como rodar o projeto

### 1. Pré-requisitos

- **Python 3.10 ou superior**, com SQLite (incluído na instalação padrão).
- Navegador atualizado.
- Internet para os gráficos via CDN e as imagens dos diagramas PlantUML.

Não é necessário instalar Node.js, npm, Java, PlantUML ou pacotes com pip. O backend usa apenas a biblioteca padrão do Python. Sem internet, a coleta e os dados locais continuam disponíveis enquanto o servidor estiver rodando; os gráficos têm alternativa nativa e os diagramas mantêm o código-fonte para consulta.

Confira o Python no terminal:

```bash
python3 --version
```

No Windows, use `py --version` e substitua `python3` por `py` nos comandos abaixo. Se o sistema só reconhecer `python`, confira se a versão é 3.10+ antes de usá-lo.

### 2. Abra o terminal dentro da pasta `atv2/`

Os comandos abaixo devem ser executados com o terminal já aberto na pasta `atv2/`, onde estão `server.py`, `schema.sql` e este README. Não é necessário informar o caminho completo do computador.

Em outro computador, use o caminho onde você salvou ou extraiu a pasta do projeto.

### 3. Inicie com dados de demonstração

```bash
python3 server.py --demo
```

No Windows:

```powershell
py server.py --demo
```

Mantenha esse terminal aberto. Quando aparecer `RotaClara: http://127.0.0.1:8000`, o servidor está pronto. A opção `--demo` cria pessoas e roteiros fictícios apenas quando a base ainda não possui motoristas. Ela não apaga nem duplica os dados existentes.

### 4. Abra no navegador

| Página | Endereço |
| --- | --- |
| Aplicativo | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| Documentação e diagramas | [http://127.0.0.1:8000/documentacao](http://127.0.0.1:8000/documentacao) |
| Campanha de divulgação | [http://127.0.0.1:8000/campanha](http://127.0.0.1:8000/campanha) |

O rodapé do aplicativo e da campanha possui o link **Documentação do trabalho**. Não abra `index.html` diretamente: o aplicativo precisa da API do servidor.

### 5. Entre com um dos perfis

| Perfil | Usuário na demonstração | Acesso |
| --- | --- | --- |
| Administrador | `admin` | Todos os cadastros, roteiros, parâmetros e auditoria |
| Gerente | `gerente` | Motoristas e roteiros da própria equipe, parâmetros e correções |
| Motorista | `motorista` | Próprios roteiros, coleta, dashboard e histórico |

**Senhas:** no primeiro início de uma base nova, a senha do `admin` aparece no terminal. As senhas aleatórias de `gerente` e `motorista` aparecem no terminal ao criar a demonstração e são salvas em `data/credenciais-demo.txt`. Guarde a senha inicial do administrador. Reiniciar o servidor não redefine as senhas; em uma base já existente, use as credenciais definidas quando ela foi criada.

Para trocar de perfil, clique em **Sair da conta** e entre novamente.

### 6. Encerre ou reinicie

Pressione **Ctrl+C** no terminal para encerrar. Para iniciar novamente, repita `python3 server.py --demo`. O banco `data/rotaclara.db` preserva os cadastros e o histórico.

## Rodar sem dados de demonstração

Em uma pasta nova, execute `python3 server.py` sem `--demo`. Isso cria somente o administrador e os parâmetros padrão. Cadastre primeiro gerente → motorista → roteiro.

Se já existe uma base e você quer testar uma nova sem alterar a anterior, informe outro arquivo. No macOS/Linux:

```bash
ROTACLARA_DB=data/nova-base.db python3 server.py --port 8001
```

No Windows PowerShell:

```powershell
$env:ROTACLARA_DB = "data/nova-base.db"
py server.py --port 8001
```

Nesse exemplo, abra `http://127.0.0.1:8001`. A variável opcional `ROTACLARA_ADMIN_PASSWORD` define a senha inicial do administrador **somente na criação de uma base sem usuários**; ela não redefine contas existentes. Para voltar à base padrão no PowerShell, abra um novo terminal ou remova a variável com `Remove-Item Env:ROTACLARA_DB`.

## Problemas comuns

| Situação | Como resolver |
| --- | --- |
| `python3` não encontrado | No Windows, tente `py`; em outros sistemas, confira `python --version` ou instale Python 3.10+ |
| Porta já em uso | Encerre a execução anterior com Ctrl+C ou use `python3 server.py --port 8001` |
| Navegador não conecta | Confirme que o servidor continua aberto e que a porta da URL corresponde à do terminal |
| Não aparece roteiro de hoje | Confira a data do filtro. A carga demo usa o dia em que foi criada; nos dias seguintes, crie um novo roteiro |
| Não consegue iniciar roteiro | O roteiro precisa estar planejado para a data atual de Brasília |
| Gerente não vê outra equipe | É o controle de acesso esperado; entre como administrador para ver todos |
| Diagrama não aparece | Confira internet/acesso a www.plantuml.com; abra o código ou baixe o .puml na mesma página |
| Senha antiga continua valendo | As variáveis de inicialização não alteram usuários existentes; use a senha original ou uma base de teste separada |

## Entregas, conforme o quadro da aula

| Parte | Conteúdo | Arquivos |
| --- | --- | --- |
| 1 — Projeto preliminar | Casos de uso completos, decisões, atores, rastreabilidade | `docs/01-projeto-preliminar.md` |
| 1 — Diagramas UML | Casos de uso, classes conceituais e robustez UC01–UC04 | `docs/diagramas/*.puml` |
| Complemento — Projeto detalhado | Componentes, implantação, classes detalhadas, objetos e modelo relacional | `docs/diagramas/*.puml` |
| 2 — Interface e interação | Dashboard dia/mês/período, coleta, equipe, parâmetros, histórico e auditoria | `static/index.html`, `static/app.js`, `static/style.css` |
| 3 — Persistência | Banco SQL, API, regras de negócio e testes | `schema.sql`, `server.py`, `rotaclara/domain.py`, `tests/` |
| Marca e campanha | Cinco nomes, slogans, justificativa, identidade visual, pitch, peças, plano de 14 dias, orçamento e métricas | `docs/04-campanha-marketing.md`, `static/campanha.html` |
| Apoio | Execução, apresentação, proteção de dados e limitações | `docs/02-operacao-e-privacidade.md`, `docs/03-validacao.md` |

Preencha nomes e matrículas dos integrantes na documentação antes de entregar. Os dados demonstrativos são fictícios.

## PlantUML

Os **11 diagramas** estão em `docs/diagramas`:

1. `casos-de-uso.puml`
2. `classes-conceitual.puml`
3. `robustez-uc01.puml`
4. `robustez-uc02.puml`
5. `robustez-uc03.puml`
6. `robustez-uc04.puml`
7. `modelo-relacional.puml`
8. `componentes.puml`
9. `implantacao.puml`
10. `classes-detalhadas.puml`
11. `objetos.puml`

Copie o conteúdo completo, incluindo `@startuml` e `@enduml`, para um editor PlantUML, como PlantText. Os 11 diagramas foram renderizados e conferidos pelo serviço PlantUML. O modelo relacional foi corrigido para declarar os atributos em linhas separadas da abertura de cada entidade. Também podem ser abertas em uma extensão PlantUML já instalada no editor. Não é necessário Mermaid.

## Regras principais

- Partida sempre com tempo zero.
- Demais paradas: saída − chegada; minutos fracionários preservados.
- Total: soma de paradas encerradas, excluindo partida.
- Combustível: distância × valor/litro ÷ km/litro.
- Jornada inicial de 8 h. Indicador agregado usa as jornadas de cada motorista/data com roteiro no período.
- Um roteiro por motorista e data; pontos numerados em ordem.
- Valores históricos são copiados para o roteiro. Alterar parâmetros não recalcula o passado.
- Correção de ponto exige gerente/admin e justificativa; registra antes/depois e recalcula o total.

## Testar

```bash
python3 -m unittest discover -s tests -v
python3 tests/benchmark.py
```

Os testes usam bancos temporários e não alteram os dados da demonstração. O benchmark cobre 12 meses, 3.650 roteiros e 36.500 pontos; mede backend local, sem rede ou renderização.

## Organização do código

`server.py` monta as dependências e inicia o servidor. O pacote `rotaclara/` separa responsabilidades:

| Arquivo | Responsabilidade |
| --- | --- |
| `http.py` | Adaptador HTTP, arquivos públicos e respostas |
| `application.py` | Fluxo da requisição: transação, autenticação e execução do endpoint |
| `dependencies.py` | Montagem das dependências que compartilham a conexão da requisição |
| `endpoints.py` e `endpoint.py` | Tabela de rotas e correspondência exata de método e caminho |
| `controllers/` | Um controlador por recurso, adaptando entrada e resposta dos endpoints |
| `services/` | Um serviço por arquivo: autenticação, equipe, roteiros, parâmetros e relatórios |
| `domain.py` e `clock.py` | Regras puras e relógio injetável, separados |
| `repositories/` | Um repositório por arquivo; consultas SQL e escopo de acesso |
| `database.py` | Unidade de trabalho: commit, rollback e fechamento da conexão |
| `security/` | Módulos separados para senhas, cookies, erros e limitação de login |
| `request.py`, `response.py` e `report_filters.py` | Objetos de entrada, resposta e filtros |
| `exporters.py` | Serialização e proteção do CSV |
| `bootstrap.py` | Inicialização do banco e dados fictícios |

Os padrões utilizados são **Service Layer**, **Repository** e **Unit of Work**, com dependências recebidas pelos construtores. Cada escrita reúne dados e auditoria na mesma transação. `BEGIN IMMEDIATE` serializa escritas concorrentes antes das leituras de validação. A resposta HTTP só é enviada depois do commit e as conexões sempre são fechadas.

Para localizar um endpoint, consulte `endpoints.py`, siga o método do controlador e então o serviço correspondente. Por exemplo: criação de roteiro → `controllers/route_controller.py` → `services/route_service.py` → `repositories/route_repository.py`. `application.py` não contém regras específicas dos recursos nem montagem de serviços. As classes de implementação ficam em arquivos próprios; somente exceções relacionadas permanecem juntas em `security/errors.py`.

No navegador, `app.js` coordena eventos e estado; `views.js` apresenta as telas; `api.js` concentra as requisições; `charts.js` gerencia Chart.js; `reporting.js` agrega paradas e `formatters.js` formata valores. São módulos nativos, sem bundler.

A divisão aplica responsabilidade única e injeção de dependências sem criar interfaces ou hierarquias sem uso. Cálculos e formatação compartilhados têm uma fonte única. Os nomes descrevem as operações e os comentários ficam reservados para contexto necessário.

Com Node.js 22 ou superior, execute os testes JavaScript com `node --test tests/frontend.test.mjs`. Node é opcional para desenvolvimento; não é necessário para rodar o aplicativo.

## Exportação

Em Histórico, aplique período, motorista e busca. **Exportar CSV** baixa os pontos filtrados. **Imprimir / salvar PDF** abre o diálogo do navegador com o mesmo recorte; selecione Salvar em PDF. Os horários do CSV são UTC (ISO 8601); a tela e a impressão usam Brasília.

## Dependências e implantação

Chart.js **4.4.8** é carregado de `https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js`. Não há npm, etapa de build ou download de biblioteca para rodar o servidor. Se a CDN não carregar, os gráficos nativos e tabelas permanecem disponíveis.

A execução é local em `127.0.0.1`; não houve publicação. Há manifesto PWA, mas não há coleta offline. Consulte as limitações e requisitos de implantação real em `docs/02-operacao-e-privacidade.md`.

Não versionar banco, senhas, documentos pessoais, sessões ou credenciais. O `.gitignore` cobre os arquivos locais de dados.

## Atualizar a documentação do site

Os textos originais ficam em `docs/*.md` e os diagramas em `docs/diagramas/*.puml`. Depois de editá-los, gere novamente a página:

```bash
python3 scripts/build_docs.py
```

O comando também incorpora este README e o esquema SQL. Ele não acessa a rede nem exige pacotes extras. Atualize a página no navegador após gerar; mudanças em `server.py` exigem reiniciar o servidor.

## Preferência de dependências

Priorizar CDN ou serviço de renderização externo quando adequado, mantendo as fontes locais. Chart.js usa jsDelivr com versão fixa; os diagramas usam o serviço PlantUML. A página de documentação envia o texto dos diagramas acadêmicos ao serviço para renderizar, sem enviar dados do banco ou credenciais.

## Autoria

Feito por Gustavo Lopes e Heitor Vieira.
