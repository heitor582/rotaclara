# Registro de validação — 20/09/2026

## Testes automatizados

Comando: `python3 -m unittest discover -s tests -v`.

Resultado: **33 testes Python passaram**. Testes do handler HTTP são executados em memória, sem sockets, usando os métodos reais de autenticação, autorização, validação e persistência em bancos SQLite temporários.

Cobertura verificada:

- RN01: partida com horário continua com zero minutos.
- RN02/RN03: roteiros A=75, B=41, C=45 minutos; minutos fracionários preservados.
- RN04: 75/480 = 15,625%; agregação de dois motoristas usa 960 minutos.
- RN07: 100 km × R$ 6/l ÷ 10 km/l = R$ 60.
- Rejeição de saída sem chegada, horários invertidos, datetime sem fuso, rendimento zero, negativo, NaN e infinito.
- Diferença temporal correta ao atravessar meia-noite com fusos diferentes.
- Login, proteção de origem, motorista impedido de alterar parâmetros ou ler auditoria.
- Isolamento de motorista e gerente da outra equipe.
- Coleta exige início do roteiro e saída do ponto anterior; última saída conclui o roteiro.
- Correção auditada, exportação filtrada e proteção contra fórmulas no CSV.
- Triggers bloqueiam exclusão da auditoria.
- Mudanças de parâmetros não alteram roteiros históricos.
- Duplicidade motorista/data rejeitada; ponto inválido desfaz toda a criação do roteiro.
- Intervalo invertido rejeitado; dados persistidos podem ser consultados em nova conexão.

Também passaram **3 testes JavaScript** com `node --test tests/frontend.test.mjs`: agregação dos gráficos, escape de HTML e conversão de fuso no editor.

Novas verificações: rollback e fechamento das conexões, escritas concorrentes sem perda de atualização, revogação de sessão no logout, senhas com espaços, correspondência exata dos endpoints, corpo e pontos inválidos, filtros de pendências e acesso aos módulos JavaScript.

A separação em controladores, serviços e repositórios foi verificada novamente pela suíte completa. Os testes adicionais confirmam que somente POST /api/login é público, que caminhos parecidos com o CSV não são aceitos e que /api/me não expõe o hash da senha. A verificação no Chrome abaixo ocorreu antes desta última reorganização de arquivos do backend.

## Desempenho do backend

Comando: `python3 tests/benchmark.py`.

Base sintética de 12 meses: 10 motoristas, 3.650 roteiros, 36.500 pontos. Cinco consultas com agregação e serialização JSON: 0,1325; 0,1228; 0,1213; 0,1237; 0,1217 segundos. Pior tempo: **0,1325 s** nesta máquina. Payload completo aproximado: **11 MB**.

Esta medição atende ao limite de 3 segundos para a parte de consulta local na carga ensaiada. Não mede transporte HTTP nem renderização de milhares de linhas. Portanto não comprova, isoladamente, RNF03 ponta a ponta em implantação real; bases maiores devem receber paginação, agregação no servidor e ensaios adicionais de interface/rede.

## Verificação após a refatoração — 20/09/2026

Chrome automatizado, servidor na porta 8001 e banco temporário separado da demonstração: login de administrador, dashboard com quatro indicadores e dois gráficos via CDN, navegação pelas seis telas, inclusão e remoção de campos de pontos com renumeração correta, filtro de pendências, logout e página de documentação com cinco documentos. Nenhum erro JavaScript observado. O servidor temporário foi encerrado após a verificação.

## Verificação no navegador em 16/09/2026, anterior à refatoração

- Login real com administrador e dashboard exibindo dados da base de demonstração.
- Gráficos de barras e rosca carregados via Chart.js/CDN.
- Navegação até Roteiros e coleta, filtro Dia e abertura do formulário de montagem.
- Viewport móvel de 390 × 844: página sem transbordamento horizontal; campos e botões se reorganizam verticalmente.
- Estrutura de impressão existente no CSS; a seleção final de Salvar em PDF depende do navegador e não foi automatizada.
- Sintaxe de Python e JavaScript verificada.

## Artefatos

11 arquivos PlantUML editáveis, documentação de casos de uso e campanha, esquema SQL, código do aplicativo, testes e guia de execução. Os 11 arquivos PlantUML foram renderizados e validados pelo serviço PlantUML no navegador, sem instalação local. O modelo relacional foi corrigido: o primeiro atributo agora fica em nova linha após a abertura de cada entidade. A página /documentacao reúne imagens, códigos-fonte, downloads e textos completos, com link nos rodapés.
