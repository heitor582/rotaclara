# Operação, proteção de dados e demonstração

## Execução local

Python 3.10 ou superior. Nenhuma biblioteca extra é necessária para rodar o aplicativo. Na pasta do projeto, executar `python3 server.py --demo` e abrir http://127.0.0.1:8000. O primeiro início imprime usuário admin e senha aleatória. A opção --demo cria pessoas e roteiros fictícios e grava as credenciais de gerente e motorista em data/credenciais-demo.txt, com permissão restrita. Não enviar esse arquivo, o banco ou senhas para repositórios públicos.

Sem --demo o banco começa vazio, com o administrador e parâmetros padrão. Cadastre primeiro um gerente, depois os motoristas e seus roteiros. A variável ROTACLARA_ADMIN_PASSWORD pode definir a senha inicial; só é usada quando não há usuário. ROTACLARA_DB permite apontar para outro arquivo de banco. O servidor aceita --port para mudar a porta e escuta apenas no computador local.

Banco: data/rotaclara.db. O histórico sobrevive à reinicialização. Parâmetros antigos ficam copiados nos roteiros. O arquivo pode ser copiado para backup com a aplicação encerrada; alternativamente, usar a API de backup do SQLite para consistência enquanto estiver em uso. Testar restauração antes de depender de backups.

### Parar o servidor

Volte ao terminal onde aparece `RotaClara: http://127.0.0.1:8000` e pressione **Ctrl+C** uma vez. O comando interrompe o servidor com segurança e libera a porta. A base `data/rotaclara.db` permanece salva; parar o servidor não apaga os dados. Para confirmar, atualize a página: ela não conseguirá mais conectar. Para rodar novamente, execute `python3 server.py --demo`.

## Roteiro de demonstração de 5–7 minutos

1. Abrir /campanha e apresentar a dor e o nome RotaClara.
2. Entrar como gerente, selecionar Mês e explicar os indicadores do conjunto fictício.
3. Abrir Roteiros e coleta, escolher Dia atual e iniciar o roteiro planejado.
4. Registrar chegada e saída na partida. Demonstrar tempo parado zero.
5. Registrar chegada no segundo ponto, aguardar alguns segundos e registrar saída. O banco mantém minutos fracionários; o cartão formata horas/minutos inteiros.
6. Consultar Histórico, buscar Rua Peru e exportar CSV. Usar Imprimir / salvar PDF para gerar o mesmo recorte.
7. Corrigir um endereço com justificativa e abrir Auditoria para mostrar antes/depois.
8. Alterar combustível e jornada e explicar que os roteiros anteriores mantêm os parâmetros originais.
9. Entrar como motorista e demonstrar ausência de acesso a correções e às rotas de outra pessoa.
10. Mostrar fontes PlantUML, esquema SQL e resultado dos testes.

Os roteiros de hoje na carga demo ficam planejados e sem horários; os seis dias anteriores possuem registros encerrados. As pessoas são fictícias e o endereço do exemplo vem do enunciado.

## Tratamento de dados no MVP

Dados tratados: nome, telefone, documento e veículo dos motoristas; nome, telefone e e-mail de gerentes; endereço/coordenadas das entregas; horários; eventos de auditoria e credenciais derivadas. Finalidade projetada: operação e análise de roteiros. Não há telemetria contínua, analytics, anúncios nem envio automatizado de mensagens.

Medidas implementadas: autorização no servidor por perfil/equipe, validação de entradas, consultas parametrizadas, senhas com PBKDF2 e salt, tokens aleatórios armazenados por hash, cookie HttpOnly/SameSite, proteção de origem em mutações, auditoria de pontos, ausência de cache de respostas pessoais e permissão 0600 no banco. Chart.js é carregado de CDN pública, portanto o navegador faz uma requisição externa para obter a biblioteca; os dados de rotas não são enviados a essa CDN pelo código do aplicativo.

Pendências organizacionais para uso real: definir controlador/operadores e finalidade específica; documentar a base legal aplicável com responsável competente; informar os profissionais; estabelecer retenção e descarte, canal de atendimento aos titulares, procedimento de correção/eliminação e resposta a incidentes; limitar acesso a backups; definir contratos e proteção do ambiente. Não se declara conformidade integral apenas pela existência do código. Este documento é um registro de decisões de projeto, não um parecer jurídico.

A versão acadêmica não possui eliminação/anomização de pessoas pela interface nem política automática de retenção. Documentos são armazenados em texto no banco protegido por permissões locais, sem criptografia de campo; para dados reais, avaliar criptografia em repouso e controles do sistema operacional. A auditoria preserva endereços e horários antigos, devendo ter retenção definida.

## Limitações técnicas explícitas

- Servidor HTTP de biblioteca padrão, adequado à demonstração local. Produção exige servidor/reverse proxy apropriado e HTTPS, além de ROTACLARA_SECURE_COOKIE=1.
- Interface adaptável e manifesto PWA; coleta requer conexão com servidor. Service worker não faz cache de dados pessoais nem sincronização offline.
- Chart.js por CDN; gráficos nativos e valores acessíveis funcionam se a biblioteca não carregar. Sem mapa ou cálculo automático de distância.
- Relatório PDF usa o diálogo de impressão do navegador, não um endpoint de geração no servidor.
- Um roteiro por motorista/data; chegada dentro dessa data e saída posterior permitida. Não existe divisão de tempo entre dias.
- Não há recuperação de senha, MFA, alteração/exclusão de contas ou gestão completa de frota. O limite de tentativas é mantido em memória e reinicia com o processo.
- Auditoria completa no banco, últimas 500 ocorrências na tela. O dono do arquivo de banco continua capaz de alterar o esquema; triggers não substituem proteção de infraestrutura.
