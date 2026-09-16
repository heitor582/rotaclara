# Registro de validação — 16/09/2026

## Testes automatizados

Comando: `python3 -m unittest discover -s tests -v`.

Resultado: **20 testes passaram**. Testes do handler HTTP são executados em memória, sem sockets, usando os métodos reais de autenticação, autorização, validação e persistência em bancos SQLite temporários.

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

## Desempenho do backend

Comando: `python3 tests/benchmark.py`.

Base sintética de 12 meses: 10 motoristas, 3.650 roteiros, 36.500 pontos. Cinco consultas com agregação e serialização JSON: 0,1181; 0,1218; 0,1198; 0,1209; 0,1207 segundos. Pior tempo: **0,1218 s** nesta máquina. Payload completo aproximado: **11 MB**.

Esta medição atende ao limite de 3 segundos para a parte de consulta local na carga ensaiada. Não mede transporte HTTP nem renderização de milhares de linhas. Portanto não comprova, isoladamente, RNF03 ponta a ponta em implantação real; bases maiores devem receber paginação, agregação no servidor e ensaios adicionais de interface/rede.

## Verificação no navegador

- Login real com administrador e dashboard exibindo dados da base de demonstração.
- Gráficos de barras e rosca carregados via Chart.js/CDN.
- Navegação até Roteiros e coleta, filtro Dia e abertura do formulário de montagem.
- Viewport móvel de 390 × 844: página sem transbordamento horizontal; campos e botões se reorganizam verticalmente.
- Estrutura de impressão existente no CSS; a seleção final de Salvar em PDF depende do navegador e não foi automatizada.
- Sintaxe de Python e JavaScript verificada.

## Artefatos

11 arquivos PlantUML editáveis, documentação de casos de uso e campanha, esquema SQL, código do aplicativo, testes e guia de execução. Os 11 arquivos PlantUML foram renderizados e validados pelo serviço PlantUML no navegador, sem instalação local. O modelo relacional foi corrigido: o primeiro atributo agora fica em nova linha após a abertura de cada entidade. A página /documentacao reúne imagens, códigos-fonte, downloads e textos completos, com link nos rodapés.
