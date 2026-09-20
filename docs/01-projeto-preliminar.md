# RotaClara — Projeto preliminar

Engenharia de Software II · Trabalho 2 · Prof. Sandro Laudares

Equipe: preencher os nomes e matrículas dos dois ou três integrantes antes da entrega.

## 1. Visão do produto

O RotaClara é um MVP web para registrar as esperas em pontos de entrega, relacioná-las a endereços e apresentar indicadores de tempo e combustível. Motoristas registram chegada e saída; gerentes analisam sua equipe; administradores gerenciam todos os cadastros.

A referência normativa do projeto é “Especificação de Requisitos — Trabalho2.pdf”, fornecida pelo professor, páginas 1–5. O texto de etapas fornecido pelo aluno organiza a execução e complementa a campanha. Em conflito, as regras explícitas do PDF foram preservadas. As duas fotos do quadro da aula de 15/09, enviadas pelo aluno, esclarecem a organização em três partes: 1ª projeto preliminar; 2ª projeto de interface e interação; 3ª projeto de persistência. O material está organizado conforme essa divisão. O quadro também menciona projeto detalhado com tecnologias, componentes, implantação, classes detalhadas e objetos, incluídos como complemento.

## 2. Escopo e decisões

Inclui RF01–RF12: cadastros, pontos com coordenadas, montagem sequencial de roteiros, coleta, cálculo, histórico, dashboard, parâmetros, estimativa de combustível e exportação. Não inclui otimização automática, ERP/folha, rastreamento veicular em tempo real ou aplicativo nativo de loja.

- Stack: Python 3.10+, API HTTP, SQLite, HTML/CSS/JavaScript e Chart.js 4.4.8 por CDN. A aplicação não depende de framework. Os cálculos e a autorização ficam no servidor.
- Ponto significa uma visita em um roteiro. Repetir um endereço em outro dia cria outro ponto, preservando os horários históricos.
- Cada roteiro tem exatamente um motorista, uma data e pelo menos dois pontos. O MVP adota um roteiro por motorista/dia, decisão adicional que evita duplicar a jornada no dashboard; não é uma restrição textual de RN05.
- Coordenadas são informadas manualmente; não há geocodificação nem cálculo automático de distância. A distância total é informada pelo responsável.
- Jornada começa com 8 horas, mas pode ser configurada. RN01–RN03 são invariantes: não é permitido incluir a partida ou alterar a fórmula para contrariar a especificação.
- Custo por km = combustível por litro ÷ rendimento. É derivado e não uma segunda cobrança. Custo do roteiro = distância × custo por km. Não representa mão de obra, manutenção, pedágios nem combustível consumido em marcha lenta.
- O rendimento específico do motorista/veículo prevalece sobre o padrão. O padrão preenche novos cadastros. Combustível, rendimento e jornada são copiados para cada roteiro na criação.
- Coleta usa relógio do servidor. Correções permitem horários manuais, exigem motivo e deixam auditoria. Dados são armazenados em UTC e exibidos no fuso America/Sao_Paulo.
- Chegada pertence à data do roteiro; saída pode atravessar a meia-noite. O tempo inteiro da visita é atribuído à data do roteiro, sem rateio diário. Não se aceitam horários futuros, sobreposição com pontos adjacentes ou saída sem chegada.
- Paradas abertas têm contador indicativo na tela, mas entram nos totais apenas após a saída. Percentuais podem superar 100%; não são truncados para ocultar jornadas excedidas.
- A jornada agregada é a soma das jornadas de motoristas/dias com roteiro, incluindo planejados. Dias sem roteiro não entram na base. A medida é uma razão ponderada, não a média simples dos percentuais.

## 3. Atores e permissões

| Ação | Motorista | Gerente | Administrador |
| --- | --- | --- | --- |
| Consultar roteiros, dashboard e histórico | Próprios | Equipe | Todos |
| Montar/iniciar roteiro e coletar horários | Próprios | Equipe | Todos |
| Cadastrar motoristas | Não | Própria equipe | Qualquer equipe |
| Cadastrar gerentes | Não | Não | Sim |
| Alterar parâmetros globais | Não | Sim | Sim |
| Corrigir pontos e consultar auditoria | Não | Equipe | Todos |
| Exportar histórico | Próprio | Equipe | Todos |

Autenticação é precondição dos casos UC01–UC07. Todas as permissões são verificadas na API; esconder um botão não é o mecanismo de segurança.

## 4. Casos de uso detalhados

### UC01 — Montar e iniciar roteiro diário

**Atores:** motorista; gerente/coordenador; administrador. **Objetivo:** criar o trajeto de uma data e habilitar a coleta. **Requisitos:** RF03, RF04, RN05, RN06.

**Pré-condições:** sessão válida; motorista cadastrado e acessível ao ator; parâmetros disponíveis. Para montar, mínimo de partida e destino. Para iniciar, roteiro planejado na data atual de Brasília.

**Fluxo principal:**

1. Ator abre Roteiros e coleta e escolhe Montar novo roteiro.
2. Seleciona motorista, data e informa distância total não negativa.
3. Insere endereços e coordenadas na sequência do trajeto, começando pela partida.
4. Sistema valida autorização, motorista, data, coordenadas, quantidade e unicidade motorista/data.
5. Sistema cria o roteiro planejado, copia parâmetros e grava pontos numerados de 1 a N em uma transação.
6. Ator seleciona Iniciar roteiro na data planejada.
7. Sistema confirma o estado e altera para em andamento, habilitando a primeira chegada.

**Alternativas e exceções:** A1: motorista autenticado só monta para si; gerente só seleciona a própria equipe. A2: novo ponto é acrescentado antes de salvar; remover um ponto renumera os restantes. E1: data/motorista duplicados retornam conflito sem gravação parcial. E2: menos de dois pontos, endereço vazio, coordenadas inválidas ou distância negativa impedem salvar. E3: iniciar fora da data ou iniciar novamente é rejeitado. E4: falha de persistência desfaz a transação; tela permite tentar novamente.

**Pós-condições de sucesso:** roteiro e pontos persistidos; parâmetros históricos preservados; criação dos pontos auditada; início deixa o roteiro em andamento. **Pós-condição de falha:** banco conserva o estado anterior.

### UC02 — Registrar chegada e saída no ponto

**Atores:** motorista; gerente; administrador. **Objetivo:** medir uma parada vinculada a endereço e horários. **Requisitos:** RF05, RF06, RN01–RN03, RN06, RNF05.

**Pré-condições:** sessão autorizada; roteiro em andamento; todos os pontos anteriores com saída registrada. Para saída, chegada já registrada no ponto.

**Fluxo principal:**

1. Ator abre o roteiro e identifica o próximo ponto pela ordem sequencial.
2. Aciona Registrar chegada.
3. Sistema valida perfil, roteiro, sequência e ausência de registro duplicado; grava horário UTC do servidor e auditoria.
4. Tela inicia contador indicativo; no ponto 1 mostra que a partida não acumula tempo.
5. Ator aciona Registrar saída.
6. Sistema valida chegada existente e cronologia; grava horário de saída.
7. Sistema calcula zero para ponto 1; para os demais, diferença saída − chegada em minutos.
8. Sistema recalcula soma do roteiro, grava auditoria e persiste tudo na mesma transação.
9. Se todos os pontos possuem saída, sistema conclui o roteiro; caso contrário habilita o próximo ponto.

**Alternativas e exceções:** A1: ponto 1 mantém horários mas tempo zero. A2: enquanto falta saída, contador é apenas visual, total persistido ainda zero. A3: erro humano é corrigido por UC07, sem sobrescrita silenciosa pelo motorista. E1: saída sem chegada, repetição ou ponto anterior pendente é rejeitado. E2: horário futuro ou cronologia incompatível é rejeitado. E3: sem conexão, tela informa erro e não confirma coleta; não existe fila offline.

**Pós-condições de sucesso:** visita, total do roteiro e auditoria consistentes. **Pós-condição de falha:** sem gravação parcial e sem avanço indevido na sequência.

### UC03 — Visualizar dashboard de tempo parado

**Atores:** gerente; administrador; motorista para os próprios dados. **Requisitos:** RF07, RF08, RN04, RNF03, RNF04.

**Pré-condições:** sessão válida. Pode haver zero roteiros no intervalo.

**Fluxo principal:**

1. Ator escolhe Dia, Mês ou Período e opcionalmente um motorista autorizado.
2. Informa a data, mês ou limites inclusivos e aplica os filtros.
3. Sistema valida datas e escopo de acesso, consultando roteiros pela data e pontos relacionados.
4. Soma tempo parado e custo estimado; calcula a base de jornada histórica por motorista/data.
5. Calcula percentual = tempo parado total ÷ base em minutos × 100.
6. Exibe KPIs, gráfico de barras diário versus jornada somada, distribuição por endereço e tabela de roteiros.
7. Ator consulta histórico para investigar os endereços com maior espera.

**Alternativas e exceções:** A1: mês é convertido do primeiro ao último dia. A2: sem roteiros, métricas zero e estado vazio. A3: sem Chart.js/internet, gráficos nativos e tabela mantêm informação acessível. A4: múltiplos motoristas somam jornadas; dois motoristas com 8 h têm base 960 min no dia. E1: fim anterior ao início é rejeitado. E2: filtro de motorista fora da equipe não revela dados. A5: paradas abertas não entram nos totais; planejados entram na base e na estimativa de combustível, conforme legenda.

**Pós-condições:** indicadores coerentes com período e perfil; nenhum dado operacional alterado.

### UC04 — Parametrizar custos e regras

**Atores:** gerente; administrador. **Requisitos:** RF09, RF10, RF11, RN04, RN07.

**Pré-condições:** sessão com perfil permitido; registro singleton de parâmetros existente.

**Fluxo principal:**

1. Ator abre Parâmetros.
2. Sistema apresenta combustível por litro, rendimento padrão, custo derivado por km, jornada e regras fixas.
3. Ator altera preço, rendimento padrão e/ou jornada.
4. Sistema exige valores finitos, combustível não negativo, rendimento positivo e jornada entre zero exclusivo e 24 h.
5. Calcula custo por km e salva parâmetros com auditoria.
6. Novos roteiros copiam os novos valores e usam o rendimento do motorista/veículo.

**Alternativas e exceções:** A1: jornada inicial é 8 h; valores fracionários são permitidos. A2: roteiros antigos mantêm snapshots. A3: não há ajuste independente de custo/km porque ele deriva da RN07. E1: motorista recebe acesso negado na API. E2: zero no rendimento, NaN, infinito ou jornada fora do limite não são gravados. A4: exclusão da partida e fórmula de diferença são exibidas como invariantes, evitando parametrização incompatível com RN01 e RN02.

**Pós-condições:** parâmetros consistentes para futuras criações, histórico preservado e alteração auditada.

### UC05 — Cadastrar equipe

**Atores:** administrador cadastra gerente e motorista; gerente cadastra motorista na própria equipe. **Pré-condições:** sessão autorizada; gerente existente para vincular motorista. **Requisitos:** RF01, RF02.

**Fluxo:** informar nome, telefone e dados do perfil (e-mail do gerente; documento, veículo e rendimento do motorista); definir usuário e senha inicial com mínimo de 10 caracteres; validar duplicidade; persistir pessoa e conta atomicamente. **Exceções:** login/documento/e-mail duplicado, vínculo inválido e campos ausentes não geram registros parciais. **Pós-condições:** pessoa e conta com perfil criadas. Manutenção/exclusão completa de contas não faz parte desta versão.

### UC06 — Consultar e exportar histórico

**Atores:** todos dentro de seu escopo. **Pré-condições:** sessão válida. **Requisitos:** RF07, RF12.

**Fluxo:** escolher período e motorista; consultar pontos; buscar endereço ou nome; exportar CSV ou abrir impressão para salvar PDF. CSV e impressão usam o mesmo período, motorista e busca. A tabela apresenta data do roteiro, endereço, chegada, saída e minutos. **Alternativas:** nenhum resultado mostra estado vazio; ponto aberto é identificado; partida aparece com zero. **Segurança:** texto potencialmente interpretado como fórmula recebe prefixo de proteção no CSV. **Pós-condições:** arquivo CSV baixado ou diálogo de impressão aberto; o usuário seleciona Salvar em PDF no navegador.

### UC07 — Corrigir ponto com auditoria

**Atores:** gerente; administrador. **Pré-condições:** acesso ao roteiro e motivo obrigatório. **Requisitos:** RNF05.

**Fluxo:** abrir correção no histórico ou coleta; revisar endereço, coordenadas e horários; informar motivo; servidor normaliza horários UTC, valida cronologia, vizinhos e data; atualiza ponto, recalcula roteiro e registra antes/depois, usuário e instante na mesma transação. **Exceções:** motorista não pode corrigir; motivo vazio, sobreposição, horário futuro, saída anterior à chegada ou remoção de saída necessária ao próximo ponto são rejeitados. **Pós-condições:** histórico corrigido e rastreável. Registros de auditoria não aceitam UPDATE/DELETE pela aplicação nem diretamente pelas operações SQL usuais, devido a triggers; acesso administrativo ao arquivo ainda exige governança.

### UC08 — Autenticar e encerrar sessão

**Atores:** todos. **Fluxo:** informar usuário/senha; verificar hash PBKDF2; criar token aleatório com validade de 8 h e cookie HttpOnly/SameSite; nas requisições seguintes validar sessão e perfil; ao sair revogar token no banco. **Exceções:** credenciais incorretas não identificam qual campo falhou; dez falhas em cinco minutos por origem limitam novas tentativas. **Pós-condições:** sessão válida ou revogada. Não há recuperação de senha por e-mail no MVP.

## 5. Modelos UML

Fontes PlantUML editáveis em docs/diagramas:

- casos-de-uso.puml: visão geral dos atores e permissões.
- classes-conceitual.puml: entidades de domínio, multiplicidades e atributos.
- robustez-uc01.puml a robustez-uc04.puml: fronteiras, controles e entidades dos quatro fluxos principais.
- modelo-relacional.puml: complemento técnico com usuário, sessão e auditoria.
- componentes.puml e implantacao.puml: arquitetura física do MVP.
- classes-detalhadas.puml e objetos.puml: estrutura lógica efetiva e exemplo do roteiro A.

Os diagramas de robustez usam actor, boundary, control e entity do PlantUML. Atores interagem com fronteiras; fronteiras com controles; controles com entidades e outros controles. Não há ligação direta de ator a entidade. No modelo conceitual, atributos com / são derivados.

## 6. Rastreabilidade

| Requisito | Implementação / evidência |
| --- | --- |
| RF01, RF02 | Equipe; API motoristas/gerentes; UC05 |
| RF03, RF04 | Novo roteiro; coordenadas e ordem; UC01 |
| RF05, RF06 | Coleta; rotaclara/domain.py; UC02 |
| RF07, RF12 | Histórico, busca, CSV e impressão PDF; UC06 |
| RF08 | Dia/mês/período; Chart.js e fallback nativo; UC03 |
| RF09–RF11 | Parâmetros, snapshot e custo; UC04 |
| RN01–RN03 | Funções de tempo e testes com A=75, B=41, C=45 min |
| RN04 | Jornada padrão 8 h; percentual ponderado; teste 75/480=15,625% |
| RN05, RN06 | FK motorista, data, UNIQUE motorista/data e roteiro/ordem |
| RN07 | distância × combustível / rendimento; teste 100×6/10=60 |
| RNF01 | SQLite, transações e schema.sql com FKs e índices |
| RNF02 | CSS responsivo, botões de 44 px, labels e navegação por teclado |
| RNF03 | Índice de data, consultas delimitadas e benchmark sintético de 12 meses |
| RNF04 | Sessão, autorização no servidor e teste de isolamento |
| RNF05 | Tabela de auditoria, antes/depois/motivo e triggers imutáveis |
| RNF06 | Minimização, restrição de acesso e plano de tratamento em 02-operacao-e-privacidade.md; conformidade integral depende da implantação |

## 7. Plano de validação e limites

Testes automatizados verificam fórmulas, validação, persistência, autenticação, permissões, coleta, correção, auditoria e exportação. O benchmark mede consulta e agregação de 12 meses em base sintética; não é garantia de desempenho de qualquer máquina ou rede. A verificação manual cobre desktop/mobile, filtros, formulários, estados vazios e impressão.

O servidor padrão escuta apenas 127.0.0.1. O MVP é adequado à execução e demonstração local, não é um serviço pronto para produção. Em produção são necessários HTTPS, servidor apropriado, gerenciamento de contas/senhas, política de retenção, rotinas de backup e processos organizacionais de proteção de dados.
