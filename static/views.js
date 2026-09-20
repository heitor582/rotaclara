import { select, selectAll, escapeHtml, formatCurrency, formatNumber, formatDuration, currentLocalDate, formatDate, formatTimestamp } from './formatters.js';
import { summarizeStops } from './reporting.js';

const formatRouteStatus = s => ({
    planejado: 'Planejado',
    em_andamento: 'Em andamento',
    concluido: 'Concluído'
}[s]);

function renderDriverOptions(people, selected = '') {
    return people.motoristas.map(m => `<option value="${m.id}" ${String(m.id) === String(selected) ? 'selected' : ''}>${escapeHtml(m.nome)}</option>`).join('');
}

function renderRouteTable(rows) {
    if (!rows.length) return '<div class="empty">Nenhum roteiro neste período. Monte o primeiro em Roteiros e coleta.</div>';
    return `<div class="table-wrap"><table><thead><tr><th>ROTEIRO / DATA</th><th>MOTORISTA</th><th>DISTÂNCIA</th><th>TEMPO PARADO</th><th>COMBUSTÍVEL ESTIMADO</th><th>SITUAÇÃO</th></tr></thead><tbody>${rows.map(r => `<tr><td><b>#${String(r.id).padStart(3, '0')}</b><small>${formatDate(r.data)}</small></td><td>${escapeHtml(r.motorista)}</td><td>${formatNumber(r.distancia_total)} km</td><td><b>${formatDuration(r.tempo_total_parado)}</b></td><td>${formatCurrency(r.custo_estimado)}</td><td><span class="badge ${r.status === 'planejado' ? 'neutral' : ''}">${formatRouteStatus(r.status)}</span></td></tr>`).join('')}</tbody></table></div>`;
}

function renderDashboard(context) {
    const { report, period } = context;
    const colors = ['#167454', '#84b780', '#bed774', '#597f91', '#a0a8bc', '#d3ab60'];
    const entries = summarizeStops(report.pontos);
    let total = entries.reduce((a, e) => a + e[1], 0),
        offset = 0;
    const gradient = entries.map((e, i) => {
        let begin = offset;
        offset += e[1] / total * 100;
        return `${colors[i]} ${begin}% ${offset}%`;
    }).join(',');
    const max = Math.max(1, ...report.dias.map(d => Math.max(d.minutos, d.jornada)));
    const best = entries[0];
    select('#view').innerHTML = `<section class="kpis" aria-label="Indicadores"><article class="kpi"><div class="kpi-label">Tempo total parado <span>◷</span></div><strong>${formatDuration(report.total_minutos)}</strong><small>Partida excluída do cálculo</small></article><article class="kpi"><div class="kpi-label">Combustível estimado <span>↗</span></div><strong>${formatCurrency(report.custo)}</strong><small>${formatNumber(report.distancia)} km em ${report.roteiros.length} roteiros</small></article><article class="kpi"><div class="kpi-label">Jornada em paradas <span>◴</span></div><strong>${formatNumber(report.percentual)}%</strong><small>Base: ${formatDuration(report.base_minutos)} de jornada</small></article><article class="kpi"><div class="kpi-label">Roteiros no período <span>⌁</span></div><strong>${report.roteiros.length.toString().padStart(2, '0')}</strong><small>${report.roteiros.filter(r => r.status === 'concluido').length} concluídos</small></article></section><section class="grid-charts"><article class="panel"><div class="panel-header"><div><h2>Tempo parado por dia</h2><p>Minutos registrados × jornada da equipe</p></div><span class="badge neutral">${period === 'dia' ? 'Dia' : period === 'mes' ? 'Mês' : 'Período'}</span></div>${report.dias.length ? `<div class="bar-chart" role="img" aria-label="Comparativo por dia; valores detalhados na tabela abaixo">${report.dias.map(d => `<div class="bar-group" title="${formatDate(d.data)}: ${formatNumber(d.minutos)} min parados / ${formatNumber(d.jornada)} min de jornada"><div class="bar" style="height:${d.minutos / max * 85}%"></div><div class="bar limit" style="height:${d.jornada / max * 85}%"></div><small>${d.data.slice(8)}/${d.data.slice(5, 7)}</small></div>`).join('')}</div><div class="legend"><span>Tempo parado</span><span>Jornada somada</span></div><details><summary>Consultar valores do gráfico</summary><table><thead><tr><th>Dia</th><th>Parado (min)</th><th>Jornada (min)</th></tr></thead><tbody>${report.dias.map(d => `<tr><td>${formatDate(d.data)}</td><td>${formatNumber(d.minutos)}</td><td>${formatNumber(d.jornada)}</td></tr>`).join('')}</tbody></table></details>` : '<div class="empty">Sem roteiros no período.</div>'}</article><article class="panel"><div class="panel-header"><div><h2>Onde o tempo se concentra</h2><p>Distribuição das paradas por endereço</p></div></div>${total ? `<div class="donut-wrap"><div class="donut" style="background:conic-gradient(${gradient})" role="img" aria-label="Distribuição por endereço listada ao lado"><div class="donut-hole"><b>${formatNumber(total)}</b><small>minutos</small></div></div><div class="point-legend">${entries.map((e, i) => `<div><i style="background:${colors[i]}"></i><span>${escapeHtml(e[0])}<small> · ${formatNumber(e[1])} min</small></span><b>${formatNumber(e[1] / total * 100)}%</b></div>`).join('')}</div></div>` : '<div class="empty">Nenhuma parada encerrada no período.</div>'}</article></section>${best ? `<div class="note"><b>Um ponto de atenção:</b> ${escapeHtml(best[0])} concentra ${formatNumber(best[1] / total * 100)}% do tempo parado. Use o histórico para investigar as esperas.</div>` : ''}<section class="panel"><div class="panel-header"><div><h2>Roteiros do período</h2><p>${formatDate(report.inicio)} a ${formatDate(report.fim)} · Valores estimados de combustível</p></div><button class="quiet" data-go="coleta">Ver roteiros →</button></div>${renderRouteTable(report.roteiros)}</section><p class="muted"><small>Percentual ponderado: minutos parados ÷ jornadas dos motoristas com roteiro no período. Paradas ainda abertas aparecem na coleta e entram nos totais após a saída. O custo usa toda a distância informada, inclusive em roteiros planejados.</small></p>`;
    const openPoints = report.pontos.filter(p => p.ordem_sequencial > 1 && p.data_hora_chegada && !p.data_hora_saida).length;
    const incompleteRoutes = report.roteiros.filter(r => r.status !== 'concluido').length;
    const avgCost = report.roteiros.length ? report.custo / report.roteiros.length : 0;
    const statusCounts = ['planejado', 'em_andamento', 'concluido'].map(status => report.roteiros.filter(r => r.status === status).length);
    const quality = document.createElement('section');
    quality.className = 'panel quality-panel';
    quality.innerHTML = `<div class="panel-header"><div><h2>Qualidade da coleta</h2><p>Status dos roteiros e pendências no filtro selecionado</p></div><button class="badge ${openPoints || incompleteRoutes ? 'neutral' : ''}" data-pending-filter>${openPoints + incompleteRoutes ? `${openPoints + incompleteRoutes} pendência(s) · ver` : 'Tudo em dia'}</button></div><div class="quality-grid"><div><b>${statusCounts[0]}</b><small>roteiro(s) planejado(s)</small></div><div><b>${statusCounts[1]}</b><small>roteiro(s) em andamento</small></div><div><b>${statusCounts[2]}</b><small>roteiro(s) concluído(s)</small></div><div><b>${openPoints}</b><small>parada(s) aberta(s)</small></div><div><b>${formatCurrency(avgCost)}</b><small>custo médio por roteiro</small></div></div>`;
    select('#view').prepend(quality);
}

function renderRoutes(context) {
    const { user, people, report } = context;
    select('#view').innerHTML = `<details class="panel" id="new-route"><summary><b>+ Montar novo roteiro</b></summary><form id="route-form"><p class="muted">Informe os pontos na ordem do trajeto. O primeiro é a partida.</p><div class="form-grid"><label>Motorista<select name="motorista_id" required>${renderDriverOptions(people, user.motorista_id)}</select></label><label>Data<input name="data" type="date" value="${currentLocalDate()}" required></label><label>Distância total (km)<input name="distancia_total" type="number" step="0.1" min="0" required></label></div><h3 style="margin-top:24px">Pontos do roteiro</h3><div id="point-inputs"></div><div class="form-actions"><button class="secondary" type="button" id="add-point">+ Adicionar ponto</button><button class="primary">Salvar roteiro</button></div></form></details>${report.roteiros.length ? report.roteiros.map(r => `<article class="panel route-card"><div class="route-header"><div><h2>Roteiro #${r.id} · ${escapeHtml(r.motorista)}</h2><p>${formatDate(r.data)} · ${formatNumber(r.distancia_total)} km · ${formatDuration(r.tempo_total_parado)} parados · ${formatCurrency(r.custo_estimado)}</p></div>${r.status === 'planejado' ? `<button class="primary" data-start="${r.id}">Iniciar roteiro</button>` : `<span class="badge">${formatRouteStatus(r.status)}</span>`}</div>${report.pontos.filter(p => p.roteiro_id === r.id).map(p => `<div class="stop ${p.data_hora_saida ? 'done' : ''}"><span class="stop-number">${p.ordem_sequencial}</span><div class="stop-body"><b>${escapeHtml(p.endereco)}</b><p>${p.ordem_sequencial === 1 ? 'Ponto de partida — não acumula tempo' : `Chegada: ${formatTimestamp(p.data_hora_chegada)} · Saída: ${formatTimestamp(p.data_hora_saida)}`}</p></div><div class="stop-actions"><span class="timer" ${p.data_hora_chegada && !p.data_hora_saida && p.ordem_sequencial > 1 ? `data-timer="${escapeHtml(p.data_hora_chegada)}"` : ''}>${formatDuration(p.tempo_parado_minutos)}</span><button class="secondary" data-arrive="${p.id}" ${r.status !== 'em_andamento' || p.data_hora_chegada ? 'disabled' : ''}>Registrar chegada</button><button class="primary" data-leave="${p.id}" ${r.status !== 'em_andamento' || !p.data_hora_chegada || p.data_hora_saida ? 'disabled' : ''}>Registrar saída</button>${user.perfil !== 'motorista' ? `<button class="quiet" data-edit="${p.id}" aria-label="Corrigir ${escapeHtml(p.endereco)}">✎</button>` : ''}</div></div>`).join('')}</article>`).join('') : '<div class="empty">Nenhum roteiro encontrado. Use “Montar novo roteiro” para começar.</div>'}`;
    appendPointInput();
    appendPointInput();
    updateStopTimers();
}

function appendPointInput() {
    const container = select('#point-inputs'),
        n = container.children.length + 1;
    const div = document.createElement('div');
    div.className = 'point-input';
    div.innerHTML = `<b>${n}</b><label>${n === 1 ? 'Partida / endereço' : 'Endereço'}<input name="endereco" required maxlength="200"></label><label>Latitude<input name="latitude" type="number" step="any" min="-90" max="90" required></label><label>Longitude<input name="longitude" type="number" step="any" min="-180" max="180" required></label><button type="button" class="quiet" data-remove-point aria-label="Remover ponto">✕</button>`;
    container.append(div);
}

function renderHistory(context) {
    const { report } = context;
    const search = context.search || '';
    select('#view').innerHTML = `<section class="panel"><div class="print-only"><h1>RotaClara · Histórico de paradas</h1><p>${formatDate(report.inicio)} a ${formatDate(report.fim)} · Horários de Brasília</p></div><div class="panel-header"><div><h2>Histórico de pontos</h2><p>${formatDate(report.inicio)} a ${formatDate(report.fim)} · ${report.pontos.length} pontos no período</p></div></div><div class="toolbar"><label class="search-label">Buscar endereço ou motorista<input id="history-search" placeholder="Ex.: Rua Peru" value="${escapeHtml(search)}"></label><button class="secondary" id="export-csv">↓ Exportar CSV</button><button class="primary" id="export-pdf">Imprimir / salvar PDF</button></div><div id="history-table" style="margin-top:24px"></div></section>`;
    renderHistoryRows(context);
}

function renderHistoryRows(context) {
    const { user, report } = context;
    let term = select('#history-search').value.toLocaleLowerCase();
    let points = report.pontos.filter(p => (p.endereco + ' ' + p.motorista).toLocaleLowerCase().includes(term));
    select('#history-table').innerHTML = `<p class="muted"><small>${points.length} pontos encontrados${term ? ' · Busca: ' + escapeHtml(term) : ''}</small></p>` + (points.length ? `<div class="table-wrap"><table><thead><tr><th>DATA / ROTEIRO</th><th>MOTORISTA</th><th>PONTO / ENDEREÇO</th><th>CHEGADA</th><th>SAÍDA</th><th>PARADO</th>${user.perfil !== 'motorista' ? '<th>AÇÃO</th>' : ''}</tr></thead><tbody>${points.map(p => `<tr><td>${formatDate(p.data)}<small>#${p.roteiro_id}</small></td><td>${escapeHtml(p.motorista)}</td><td>${p.ordem_sequencial}. ${escapeHtml(p.endereco)}${p.ordem_sequencial === 1 ? '<small>Partida · excluída</small>' : ''}</td><td>${formatTimestamp(p.data_hora_chegada)}</td><td>${formatTimestamp(p.data_hora_saida)}</td><td>${formatDuration(p.tempo_parado_minutos)}${p.data_hora_chegada && !p.data_hora_saida ? '<small>Em aberto</small>' : ''}</td>${user.perfil !== 'motorista' ? `<td><button class="quiet" data-edit="${p.id}">Corrigir</button></td>` : ''}</tr>`).join('')}</tbody></table></div>` : '<div class="empty">Nenhum ponto encontrado com esses filtros.</div>');
}

function renderTeam(context) {
    const { user, people, params } = context;
    select('#view').innerHTML = `<div class="note">Cada cadastro cria uma conta com perfil próprio. Gerentes acessam apenas os motoristas de sua equipe.</div><section class="panel"><h2>Motoristas</h2>${people.motoristas.length ? `<div class="table-wrap"><table><thead><tr><th>NOME</th><th>TELEFONE</th><th>VEÍCULO</th><th>KM/L</th><th>GERENTE</th></tr></thead><tbody>${people.motoristas.map(m => `<tr><td>${escapeHtml(m.nome)}</td><td>${escapeHtml(m.telefone)}</td><td>${escapeHtml(m.veiculo)}</td><td>${formatNumber(m.km_por_litro)}</td><td>${escapeHtml(people.gerentes.find(g => g.id === m.gerente_id)?.nome || '—')}</td></tr>`).join('')}</tbody></table></div>` : '<p class="muted">Nenhum motorista cadastrado.</p>'}<details style="margin-top:20px"><summary><b>+ Cadastrar motorista</b></summary><form id="driver-form" style="margin-top:20px"><div class="form-grid">${renderFormField('nome', 'Nome')}${renderFormField('telefone', 'Telefone', 'tel')}${renderFormField('documento', 'Documento')}${renderFormField('veiculo', 'Veículo')}${renderFormField('km_por_litro', 'Rendimento (km/l)', 'number', 'step="0.01" min="0.01" value="' + params.km_por_litro + '"')}<label>Gerente responsável<select name="gerente_id" required>${people.gerentes.map(g => `<option value="${g.id}">${escapeHtml(g.nome)}</option>`).join('')}</select></label>${renderFormField('login', 'Usuário de acesso')}${renderFormField('senha', 'Senha inicial', 'password', 'minlength="10" autocomplete="new-password"')}</div><div class="form-actions"><button class="primary">Cadastrar motorista</button></div></form></details></section><section class="panel"><h2>Gerentes</h2><div class="table-wrap"><table><thead><tr><th>NOME</th><th>E-MAIL</th><th>TELEFONE</th></tr></thead><tbody>${people.gerentes.map(g => `<tr><td>${escapeHtml(g.nome)}</td><td>${escapeHtml(g.email)}</td><td>${escapeHtml(g.telefone)}</td></tr>`).join('')}</tbody></table></div>${user.perfil === 'administrador' ? `<details style="margin-top:20px"><summary><b>+ Cadastrar gerente</b></summary><form id="manager-form" style="margin-top:20px"><div class="form-grid">${renderFormField('nome', 'Nome')}${renderFormField('telefone', 'Telefone', 'tel')}${renderFormField('email', 'E-mail', 'email')}${renderFormField('login', 'Usuário de acesso')}${renderFormField('senha', 'Senha inicial', 'password', 'minlength="10" autocomplete="new-password"')}</div><div class="form-actions"><button class="primary">Cadastrar gerente</button></div></form></details>` : ''}</section>`;
}

function renderFormField(name, label, type = 'text', attrs = '') {
    return `<label>${label}<input name="${name}" type="${type}" ${attrs} required maxlength="200"></label>`;
}

function renderSettings(context) {
    const { params } = context;
    select('#view').innerHTML = `<section class="panel"><h2>Parâmetros de custo e jornada</h2><p class="muted">Aplicados aos novos roteiros. O histórico mantém os valores originais.</p><form id="settings-form"><div class="form-grid">${renderFormField('valor_combustivel', 'Combustível (R$/litro)', 'number', `step="0.01" min="0" value="${params.valor_combustivel}"`)}${renderFormField('km_por_litro', 'Rendimento padrão (km/l)', 'number', `step="0.01" min="0.01" value="${params.km_por_litro}"`)}${renderFormField('jornada_padrao_horas', 'Jornada diária (horas)', 'number', `step="0.25" min="0.25" max="24" value="${params.jornada_padrao_horas}"`)}<label>Custo padrão por km (R$)<input id="cost-km" readonly value="${formatNumber(params.custo_por_km)}"></label></div><p class="note" style="margin-top:22px">O custo por km é calculado pelo preço do combustível ÷ rendimento. Cada roteiro usa o rendimento cadastrado no veículo do motorista. O padrão acima preenche novos cadastros.</p><h3>Regras do tempo parado</h3><p class="muted">Ponto 1 sempre excluído · Tempo = saída − chegada · Total = soma das paradas encerradas. Estas regras são obrigatórias na especificação e permanecem fixas.</p><div class="form-actions"><button class="primary">Salvar parâmetros</button></div></form></section>`;
}

function renderAudit(rows) {
    select('#view').innerHTML = `<section class="panel"><h2>Registro de alterações</h2><p class="muted">Últimos 500 registros acessíveis ao seu perfil. O histórico completo permanece no banco.</p>${rows.length ? `<div class="table-wrap"><table><thead><tr><th>QUANDO / QUEM</th><th>PONTO</th><th>AÇÃO / MOTIVO</th><th>ALTERAÇÕES</th></tr></thead><tbody>${rows.map(a => { const before = JSON.parse(a.antes), after = JSON.parse(a.depois); const changes = Object.keys(after).filter(k => JSON.stringify(before[k]) !== JSON.stringify(after[k])).map(k => `<div><b>${escapeHtml(k)}</b>: ${escapeHtml(before[k] ?? '—')} → ${escapeHtml(after[k] ?? '—')}</div>`).join(''); return `<tr><td>${formatTimestamp(a.instante)}<small>${escapeHtml(a.login)}</small></td><td>${a.ponto_id ? '#' + a.ponto_id : 'Parâmetros'}</td><td>${escapeHtml(a.acao)}<small>${escapeHtml(a.motivo)}</small></td><td><details><summary>Ver alterações</summary>${changes || 'Sem mudança de valores'}</details></td></tr>`; }).join('')}</tbody></table></div>` : '<div class="empty">Nenhuma alteração registrada.</div>'}</section>`;
}

function updateStopTimers() {
    selectAll('[data-timer]').forEach(el => el.textContent = formatDuration(Math.max(0, (Date.now() - Date.parse(el.dataset.timer)) / 60000)));
}

export { renderDriverOptions, renderRouteTable, renderDashboard, renderRoutes, appendPointInput, renderHistory, renderHistoryRows, renderTeam, renderFormField, renderSettings, renderAudit, updateStopTimers };
