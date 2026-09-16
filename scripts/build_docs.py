"""Gera página de documentação com fontes locais; não acessa a rede.
Executar: python3 scripts/build_docs.py
Imagens são renderizadas pelo serviço PlantUML ao abrir a página.
"""
from pathlib import Path
import re
import html
import zlib

ROOT = Path(__file__).resolve().parents[1]

def inline(value):
    value = html.escape(value)
    value = re.sub(r'`([^`]+)`',r'<code>\1</code>',value)
    value = re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',value)
    return value


def markdown(source):
    lines=source.splitlines(); out=[]; i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'): code.append(lines[i]);i+=1
            out.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>');i+=1;continue
        if line.startswith('#'):
            m=re.match(r'^(#{1,6}) (.*)$',line)
            if m:
                level=min(6,len(m[1])+1)
                out.append(f'<h{level}>{inline(m[2])}</h{level}>');i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                parts=[p.strip() for p in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',p) for p in parts): rows.append(parts)
                i+=1
            out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows[1:])+'</tbody></table></div>');continue
        if re.match(r'^(\d+\. |[-*] )',line):
            numbered=bool(re.match(r'^\d+\. ',line));tag='ol' if numbered else 'ul';items=[]
            pattern=r'^\d+\. ' if numbered else r'^[-*] '
            while i<len(lines) and re.match(pattern,lines[i].strip()):
                items.append('<li>'+inline(re.sub(pattern,'',lines[i].strip()))+'</li>');i+=1
            out.append(f'<{tag}>'+''.join(items)+f'</{tag}>');continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|\d+\. |[-*] )',lines[i].strip()):
            paragraph.append(lines[i].strip());i+=1
        out.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '\n'.join(out)


def plantuml_url(source):
    alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    compressor=zlib.compressobj(9,zlib.DEFLATED,-15)
    data=compressor.compress(source.encode())+compressor.flush()
    output=''
    for i in range(0,len(data),3):
        chunk=data[i:i+3]+b'\x00\x00'
        b1,b2,b3=chunk[:3]
        output+=''.join(alphabet[n] for n in [b1>>2,((b1&3)<<4)|(b2>>4),((b2&15)<<2)|(b3>>6),b3&63])
    return 'https://www.plantuml.com/plantuml/svg/'+output


def diagram(file,title,description):
    source=(ROOT/'docs/diagramas'/file).read_text()
    url=plantuml_url(source);label=html.escape(title)
    return f'''<article class="diagram-card" id="{file[:-5]}"><div class="diagram-heading"><div><h3>{label}</h3><p>{html.escape(description)}</p></div><a class="download" href="/documentacao/arquivos/{file}" download>Baixar .puml ↓</a></div>
    <a class="diagram-image" href="{url}" target="_blank" rel="noopener noreferrer" aria-label="Ampliar diagrama: {label}"><img loading="lazy" src="{url}" alt="Diagrama PlantUML: {label}"></a>
    <p class="image-error" hidden>Não foi possível carregar a imagem. O código e o arquivo PlantUML estão disponíveis abaixo.</p>
    <details class="source"><summary>Ver código PlantUML</summary><button class="copy-code secondary" type="button">Copiar código</button><pre><code>{html.escape(source)}</code></pre></details></article>'''


def document(file,title,description):
    return f'''<details class="doc-document"><summary><span><strong>{title}</strong><small>{description}</small></span><span class="expand-label">Ler documento +</span></summary><div class="document-content"><a class="download" href="/documentacao/arquivos/{file}" download>Baixar original .md ↓</a>{markdown((ROOT/'README.md' if file=='README.md' else ROOT/'docs'/file).read_text())}</div></details>'''

sections=[
('preliminar','01','Projeto preliminar','Especificação dos casos de uso, classes conceituais e diagramas de robustez.',[
('casos-de-uso.puml','Casos de uso','Atores, funcionalidades e permissões.'),
('classes-conceitual.puml','Classes conceituais','Entidades do domínio, atributos e multiplicidades.'),
('robustez-uc01.puml','UC01 · Montar e iniciar roteiro','Interação entre tela, controles e entidades na criação do roteiro.'),
('robustez-uc02.puml','UC02 · Registrar chegada e saída','Validação, cálculo do tempo parado e auditoria.'),
('robustez-uc03.puml','UC03 · Consultar dashboard','Consulta por período e agregação dos indicadores.'),
('robustez-uc04.puml','UC04 · Parametrizar custos e jornada','Configuração dos valores aplicados a novos roteiros.')]),
('detalhado','02','Projeto detalhado','Tecnologias e modelos de arquitetura física e lógica citados no quadro.',[
('componentes.puml','Diagrama de componentes','Interface, API, regras de negócio e persistência.'),
('implantacao.puml','Diagrama de implantação','Navegador, servidor Python local, SQLite e CDN.'),
('classes-detalhadas.puml','Classes detalhadas','Estrutura efetiva dos módulos Python e do servidor HTTP.'),
('objetos.puml','Diagrama de objetos','Instâncias do roteiro A: 75 minutos parados.')]),
('persistencia','03','Projeto de persistência','Modelo físico de dados, chaves e relacionamentos.',[
('modelo-relacional.puml','Modelo relacional','Gerentes, motoristas, roteiros, pontos, parâmetros, usuários, sessões e auditoria.')])]
body=[]
for sid,number,title,desc,diagrams in sections:
    extra=''
    if sid=='preliminar': extra=document('01-projeto-preliminar.md','Especificação completa dos casos de uso','Pré-condições, fluxos principais, alternativas, pós-condições e rastreabilidade.')
    if sid=='detalhado': extra='<div class="note"><b>Interface e interação — 2ª parte da entrega:</b> o aplicativo reúne coleta, dashboard, histórico, equipe, parâmetros e auditoria. <a href="/">Abrir o MVP →</a><br>Os diagramas abaixo complementam o projeto conforme os itens de arquitetura escritos no quadro.</div>'
    if sid=='persistencia': extra='<p><a class="download" href="/documentacao/arquivos/schema.sql" download>Baixar esquema SQL completo ↓</a></p><details class="source"><summary>Consultar esquema SQL</summary><pre><code>'+html.escape((ROOT/'schema.sql').read_text())+'</code></pre></details>'
    body.append(f'<section class="docs-section" id="{sid}"><div class="section-heading"><span>{number}</span><div><h2>{title}</h2><p>{desc}</p></div></div>{extra}'+''.join(diagram(*d) for d in diagrams)+'</section>')
body.append('<section class="docs-section" id="campanha"><div class="section-heading"><span>04</span><div><h2>Marca e campanha</h2><p>Nome do produto, identidade e divulgação para os pontos extras.</p></div></div>'+ '<div id="campanha-marketing">' + document('04-campanha-marketing.md','Campanha de marketing','Nome, identidade visual, peças, cronograma, orçamento e métricas.').replace('<details class="doc-document">','<details class="doc-document" open>',1) + '</div><p><a class="download" href="/campanha">Abrir landing page da campanha ↗</a></p></section>')
body.append('<section class="docs-section" id="apoio"><div class="section-heading"><span>05</span><div><h2>Operação e validação</h2><p>Como executar, apresentar e verificar o projeto.</p></div></div>'+document('README.md','Como rodar o projeto','Pré-requisitos, comandos, endereços, perfis de acesso e solução de problemas.')+document('02-operacao-e-privacidade.md','Operação e proteção de dados','Execução local, roteiro de demonstração e limitações do MVP.')+document('03-validacao.md','Registro de validação','Testes de negócio e API, desempenho e verificação da interface.')+'</section>')
page='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#102b36"><title>Documentação do trabalho · RotaClara</title><link rel="icon" href="/icon.svg"><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/docs.css"><script src="/docs.js" defer></script></head><body class="docs-page"><header class="docs-top"><a class="brand" href="/"><span class="brand-icon">r.</span>rota<span>clara</span></a><a class="secondary" href="/">Voltar ao aplicativo ↗</a></header><main class="docs-main"><div class="docs-intro"><div class="eyebrow">ENGENHARIA DE SOFTWARE II · TRABALHO 2</div><h1>Documentação do trabalho</h1><p>Casos de uso, diagramas e materiais da RotaClara, reunidos para consulta e apresentação.</p><div class="docs-meta"><span>1ª parte · Projeto preliminar</span><span>2ª parte · Interface e interação</span><span>3ª parte · Persistência</span></div></div><nav class="docs-toc" aria-label="Seções da documentação"><a href="#preliminar">Projeto preliminar</a><a href="#detalhado">Projeto detalhado</a><a href="#persistencia">Persistência</a><a href="#campanha-marketing">Campanha de marketing</a><a href="#apoio">Operação e testes</a></nav><p class="docs-notice">Os diagramas são gerados pelo serviço PlantUML e precisam de internet. Clique na imagem para ampliar. Os documentos e códigos-fonte ficam disponíveis nesta página.</p>'''+''.join(body)+'''<footer><span>RotaClara · Documentação acadêmica</span><span>Feito por Gustavo Lopes e Heitor Vieira</span><a href="#">Voltar ao topo ↑</a><a href="/">Abrir aplicativo</a></footer></main><div id="toast" role="status" aria-live="polite" hidden></div></body></html>'''
(ROOT/'static/documentacao.html').write_text(page)
print(f'Página gerada com {sum(len(s[4]) for s in sections)} diagramas e 6 documentos.')
