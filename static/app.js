'use strict';
const $ = s => document.querySelector(s),
    $$ = s => [...document.querySelectorAll(s)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}[c]));
const money = v => Number(v).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
});
const num = v => Number(v).toLocaleString('pt-BR', {
    maximumFractionDigits: 1
});
const duration = v => `${Math.floor(v / 60)}h ${Math.floor(v % 60).toString().padStart(2, '0')}min`;
const localDay = () => new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
}).format(new Date());
const dateBR = v => v ? new Date(v + 'T12:00:00').toLocaleDateString('pt-BR') : '—';
const stamp = v => v ? new Date(v).toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo'
}) : '—';
const dateInput = v => v ? new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
}).format(new Date(v)).replace(' ', 'T') : '';
let user, people = {
    motoristas: [],
    gerentes: []
},
    params, report, view = 'dashboard',
    period = 'mes',
    renderId = 0;
let toastTimer;
let charts = [];

function toast(message) {
    $('#toast').textContent = message;
    $('#toast').hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $('#toast').hidden = true, 6000);
}
async function api(path, method = 'GET', data) {
    const res = await fetch('/api' + path, {
        method,
        headers: method === 'GET' ? {} : {
            'Content-Type': 'application/json',
            'X-RotaClara': '1'
        },
        body: data === undefined ? undefined : JSON.stringify(data)
    });
    const result = await res.json();
    if (!res.ok) {
        if (res.status === 401 && path !== '/login') showLogin();
        throw Error(result.erro || 'Não foi possível concluir.');
    }
    return result;
}
const formData = form => Object.fromEntries(new FormData(form));
async function action(button, fn) {
    if (button) button.disabled = true;
    try {
        await fn();
    } catch (e) {
        toast(e.message);
    } finally {
        if (button) button.disabled = false;
    }
}

function showLogin() {
    $('#app').hidden = true;
    $('#login-screen').hidden = false;
    user = null;
}

function range() {
    if (period === 'dia') return [$('#day').value, $('#day').value];
    if (period === 'mes') {
        let m = $('#month').value;
        let [y, n] = m.split('-').map(Number);
        return [m + '-01', m + '-' + new Date(y, n, 0).getDate()];
    }
    return [$('#start').value, $('#end').value];
}

function query(search = '') {
    const [a, b] = range();
    return new URLSearchParams({
        inicio: a,
        fim: b,
        motorista: $('#driver-filter').value,
        busca: search
    }).toString();
}

function driverOptions(selected = '') {
    return people.motoristas.map(m => `<option value="${m.id}" ${String(m.id) === String(selected) ? 'selected' : ''}>${esc(m.nome)}</option>`).join('');
}
async function boot() {
    try {
        user = await api('/me');
        [people, params] = await Promise.all([api('/pessoas'), api('/parametros')]);
        $('#login-screen').hidden = true;
        $('#app').hidden = false;
        $('#user-name').textContent = user.login;
        $('#user-role').textContent = user.perfil;
        $$('[data-manager]').forEach(el => el.hidden = user.perfil === 'motorista');
        $('#driver-filter').innerHTML = '<option value="">Todos os motoristas</option>' + driverOptions();
        if (user.perfil === 'motorista') {
            $('#driver-filter').value = user.motorista_id;
            view = 'coleta';
            period = 'dia';
            setPeriod('dia');
        }
        await render();
    } catch (e) {
        showLogin();
    }
}

function setPeriod(p) {
    period = p;
    $$('[data-period]').forEach(b => b.classList.toggle('active', b.dataset.period === p));
    $('#day-filter').hidden = p !== 'dia';
    $('#month-filter').hidden = p !== 'mes';
    $('#start-filter').hidden = $('#end-filter').hidden = p !== 'periodo';
}
const titles = {
    dashboard: ['Cada minuto, à vista.', 'Tempo parado e custo estimado dos seus roteiros.', 'VISÃO GERAL'],
    coleta: ['O trajeto começa aqui.', 'Organize os pontos e registre cada chegada e saída.', 'ROTEIROS E COLETA'],
    historico: ['O caminho fica registrado.', 'Consulte paradas por endereço e exporte o período.', 'HISTÓRICO'],
    pessoas: ['Quem move a operação.', 'Cadastre profissionais e organize a equipe responsável.', 'EQUIPE'],
    parametros: ['Os números da sua operação.', 'Configure os valores usados nos próximos roteiros.', 'PARÂMETROS'],
    auditoria: ['Cada alteração, rastreável.', 'Consulte quem alterou pontos, horários e parâmetros.', 'AUDITORIA']
};
async function render() {
    const id = ++renderId;
    const t = titles[view];
    $('#page-title').textContent = t[0];
    $('#page-subtitle').textContent = t[1];
    $('#breadcrumb').textContent = t[2];
    $$('[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
    $('#filters').hidden = !['dashboard', 'coleta', 'historico'].includes(view);
    $('#view').innerHTML = '<div class="empty" role="status">Carregando dados…</div>';
    try {
        if (['dashboard', 'coleta', 'historico'].includes(view)) {
            const result = await api('/relatorio?' + query());
            if (id !== renderId) return;
            report = result;
        }
        if (view === 'dashboard') { dashboard(); enhanceCharts(); }
        if (view === 'coleta') routes();
        if (view === 'historico') history();
        if (view === 'pessoas') {
            people = await api('/pessoas');
            if (id === renderId) team();
        }
        if (view === 'parametros') {
            params = await api('/parametros');
            if (id === renderId) settings();
        }
        if (view === 'auditoria') {
            const rows = await api('/auditoria');
            if (id === renderId) audit(rows);
        }
    } catch (e) {
        if (id === renderId) $('#view').innerHTML = `<div class="empty error">${esc(e.message)}</div>`;
    }
}

function routeTable(rows) {
    if (!rows.length) return '<div class="empty">Nenhum roteiro neste período. Monte o primeiro em Roteiros e coleta.</div>';
    return `<div class="table-wrap"><table><thead><tr><th>ROTEIRO / DATA</th><th>MOTORISTA</th><th>DISTÂNCIA</th><th>TEMPO PARADO</th><th>COMBUSTÍVEL ESTIMADO</th><th>SITUAÇÃO</th></tr></thead><tbody>${rows.map(r => `<tr><td><b>#${String(r.id).padStart(3, '0')}</b><small>${dateBR(r.data)}</small></td><td>${esc(r.motorista)}</td><td>${num(r.distancia_total)} km</td><td><b>${duration(r.tempo_total_parado)}</b></td><td>${money(r.custo_estimado)}</td><td><span class="badge ${r.status === 'planejado' ? 'neutral' : ''}">${statusName(r.status)}</span></td></tr>`).join('')}</tbody></table></div>`;
}
const statusName = s => ({
    planejado: 'Planejado',
    em_andamento: 'Em andamento',
    concluido: 'Concluído'
}[s]);

function dashboard() {
    charts.forEach(c => c.destroy()); charts = [];
    const colors = ['#167454', '#84b780', '#bed774', '#597f91', '#a0a8bc', '#d3ab60'];
    let groups = {};
    report.pontos.filter(p => p.ordem_sequencial > 1).forEach(p => groups[p.endereco] = (groups[p.endereco] || 0) + p.tempo_parado_minutos);
    let entries = Object.entries(groups).filter(e => e[1] > 0).sort((a, b) => b[1] - a[1]);
    if (entries.length > 5) entries = [...entries.slice(0, 5), ['Outros', entries.slice(5).reduce((a, b) => a + b[1], 0)]];
    let total = entries.reduce((a, e) => a + e[1], 0),
        offset = 0;
    const gradient = entries.map((e, i) => {
        let begin = offset;
        offset += e[1] / total * 100;
        return `${colors[i]} ${begin}% ${offset}%`;
    }).join(',');
    const max = Math.max(1, ...report.dias.map(d => Math.max(d.minutos, d.jornada)));
    const best = entries[0];
    $('#view').innerHTML = `<section class="kpis" aria-label="Indicadores"><article class="kpi"><div class="kpi-label">Tempo total parado <span>◷</span></div><strong>${duration(report.total_minutos)}</strong><small>Partida excluída do cálculo</small></article><article class="kpi"><div class="kpi-label">Combustível estimado <span>↗</span></div><strong>${money(report.custo)}</strong><small>${num(report.distancia)} km em ${report.roteiros.length} roteiros</small></article><article class="kpi"><div class="kpi-label">Jornada em paradas <span>◴</span></div><strong>${num(report.percentual)}%</strong><small>Base: ${duration(report.base_minutos)} de jornada</small></article><article class="kpi"><div class="kpi-label">Roteiros no período <span>⌁</span></div><strong>${report.roteiros.length.toString().padStart(2, '0')}</strong><small>${report.roteiros.filter(r => r.status === 'concluido').length} concluídos</small></article></section><section class="grid-charts"><article class="panel"><div class="panel-header"><div><h2>Tempo parado por dia</h2><p>Minutos registrados × jornada da equipe</p></div><span class="badge neutral">${period === 'dia' ? 'Dia' : period === 'mes' ? 'Mês' : 'Período'}</span></div>${report.dias.length ? `<div class="bar-chart" role="img" aria-label="Comparativo por dia; valores detalhados na tabela abaixo">${report.dias.map(d => `<div class="bar-group" title="${dateBR(d.data)}: ${num(d.minutos)} min parados / ${num(d.jornada)} min de jornada"><div class="bar" style="height:${d.minutos / max * 85}%"></div><div class="bar limit" style="height:${d.jornada / max * 85}%"></div><small>${d.data.slice(8)}/${d.data.slice(5, 7)}</small></div>`).join('')}</div><div class="legend"><span>Tempo parado</span><span>Jornada somada</span></div><details><summary>Consultar valores do gráfico</summary><table><thead><tr><th>Dia</th><th>Parado (min)</th><th>Jornada (min)</th></tr></thead><tbody>${report.dias.map(d => `<tr><td>${dateBR(d.data)}</td><td>${num(d.minutos)}</td><td>${num(d.jornada)}</td></tr>`).join('')}</tbody></table></details>` : '<div class="empty">Sem roteiros no período.</div>'}</article><article class="panel"><div class="panel-header"><div><h2>Onde o tempo se concentra</h2><p>Distribuição das paradas por endereço</p></div></div>${total ? `<div class="donut-wrap"><div class="donut" style="background:conic-gradient(${gradient})" role="img" aria-label="Distribuição por endereço listada ao lado"><div class="donut-hole"><b>${num(total)}</b><small>minutos</small></div></div><div class="point-legend">${entries.map((e, i) => `<div><i style="background:${colors[i]}"></i><span>${esc(e[0])}<small> · ${num(e[1])} min</small></span><b>${num(e[1] / total * 100)}%</b></div>`).join('')}</div></div>` : '<div class="empty">Nenhuma parada encerrada no período.</div>'}</article></section>${best ? `<div class="note"><b>Um ponto de atenção:</b> ${esc(best[0])} concentra ${num(best[1] / total * 100)}% do tempo parado. Use o histórico para investigar as esperas.</div>` : ''}<section class="panel"><div class="panel-header"><div><h2>Roteiros do período</h2><p>${dateBR(report.inicio)} a ${dateBR(report.fim)} · Valores estimados de combustível</p></div><button class="quiet" data-go="coleta">Ver roteiros →</button></div>${routeTable(report.roteiros)}</section><p class="muted"><small>Percentual ponderado: minutos parados ÷ jornadas dos motoristas com roteiro no período. Paradas ainda abertas aparecem na coleta e entram nos totais após a saída. O custo usa toda a distância informada, inclusive em roteiros planejados.</small></p>`;
}

function routes() {
    $('#view').innerHTML = `<details class="panel" id="new-route"><summary><b>+ Montar novo roteiro</b></summary><form id="route-form"><p class="muted">Informe os pontos na ordem do trajeto. O primeiro é a partida.</p><div class="form-grid"><label>Motorista<select name="motorista_id" required>${driverOptions(user.motorista_id)}</select></label><label>Data<input name="data" type="date" value="${localDay()}" required></label><label>Distância total (km)<input name="distancia_total" type="number" step="0.1" min="0" required></label></div><h3 style="margin-top:24px">Pontos do roteiro</h3><div id="point-inputs"></div><div class="form-actions"><button class="secondary" type="button" id="add-point">+ Adicionar ponto</button><button class="primary">Salvar roteiro</button></div></form></details>${report.roteiros.length ? report.roteiros.map(r => `<article class="panel route-card"><div class="route-header"><div><h2>Roteiro #${r.id} · ${esc(r.motorista)}</h2><p>${dateBR(r.data)} · ${num(r.distancia_total)} km · ${duration(r.tempo_total_parado)} parados · ${money(r.custo_estimado)}</p></div>${r.status === 'planejado' ? `<button class="primary" data-start="${r.id}">Iniciar roteiro</button>` : `<span class="badge">${statusName(r.status)}</span>`}</div>${report.pontos.filter(p => p.roteiro_id === r.id).map(p => `<div class="stop ${p.data_hora_saida ? 'done' : ''}"><span class="stop-number">${p.ordem_sequencial}</span><div class="stop-body"><b>${esc(p.endereco)}</b><p>${p.ordem_sequencial === 1 ? 'Ponto de partida — não acumula tempo' : `Chegada: ${stamp(p.data_hora_chegada)} · Saída: ${stamp(p.data_hora_saida)}`}</p></div><div class="stop-actions"><span class="timer" ${p.data_hora_chegada && !p.data_hora_saida && p.ordem_sequencial > 1 ? `data-timer="${esc(p.data_hora_chegada)}"` : ''}>${duration(p.tempo_parado_minutos)}</span><button class="secondary" data-arrive="${p.id}" ${r.status !== 'em_andamento' || p.data_hora_chegada ? 'disabled' : ''}>Registrar chegada</button><button class="primary" data-leave="${p.id}" ${r.status !== 'em_andamento' || !p.data_hora_chegada || p.data_hora_saida ? 'disabled' : ''}>Registrar saída</button>${user.perfil !== 'motorista' ? `<button class="quiet" data-edit="${p.id}" aria-label="Corrigir ${esc(p.endereco)}">✎</button>` : ''}</div></div>`).join('')}</article>`).join('') : '<div class="empty">Nenhum roteiro encontrado. Use “Montar novo roteiro” para começar.</div>'}`;
    addPoint();
    addPoint();
    updateTimers();
}

function addPoint() {
    const container = $('#point-inputs'),
        n = container.children.length + 1;
    const div = document.createElement('div');
    div.className = 'point-input';
    div.innerHTML = `<b>${n}</b><label>${n === 1 ? 'Partida / endereço' : 'Endereço'}<input name="endereco" required maxlength="200"></label><label>Latitude<input name="latitude" type="number" step="any" min="-90" max="90" required></label><label>Longitude<input name="longitude" type="number" step="any" min="-180" max="180" required></label><button type="button" class="quiet" data-remove-point aria-label="Remover ponto">✕</button>`;
    container.append(div);
}

function history() {
    const search = $('#history-search')?.value || '';
    $('#view').innerHTML = `<section class="panel"><div class="print-only"><h1>RotaClara · Histórico de paradas</h1><p>${dateBR(report.inicio)} a ${dateBR(report.fim)} · Horários de Brasília</p></div><div class="panel-header"><div><h2>Histórico de pontos</h2><p>${dateBR(report.inicio)} a ${dateBR(report.fim)} · ${report.pontos.length} pontos no período</p></div></div><div class="toolbar"><label class="search-label">Buscar endereço ou motorista<input id="history-search" placeholder="Ex.: Rua Peru" value="${esc(search)}"></label><button class="secondary" id="export-csv">↓ Exportar CSV</button><button class="primary" id="export-pdf">Imprimir / salvar PDF</button></div><div id="history-table" style="margin-top:24px"></div></section>`;
    historyRows();
}

function historyRows() {
    let term = $('#history-search').value.toLocaleLowerCase();
    let points = report.pontos.filter(p => (p.endereco + ' ' + p.motorista).toLocaleLowerCase().includes(term));
    $('#history-table').innerHTML = `<p class="muted"><small>${points.length} pontos encontrados${term ? ' · Busca: ' + esc(term) : ''}</small></p>` + (points.length ? `<div class="table-wrap"><table><thead><tr><th>DATA / ROTEIRO</th><th>MOTORISTA</th><th>PONTO / ENDEREÇO</th><th>CHEGADA</th><th>SAÍDA</th><th>PARADO</th>${user.perfil !== 'motorista' ? '<th>AÇÃO</th>' : ''}</tr></thead><tbody>${points.map(p => `<tr><td>${dateBR(p.data)}<small>#${p.roteiro_id}</small></td><td>${esc(p.motorista)}</td><td>${p.ordem_sequencial}. ${esc(p.endereco)}${p.ordem_sequencial === 1 ? '<small>Partida · excluída</small>' : ''}</td><td>${stamp(p.data_hora_chegada)}</td><td>${stamp(p.data_hora_saida)}</td><td>${duration(p.tempo_parado_minutos)}${p.data_hora_chegada && !p.data_hora_saida ? '<small>Em aberto</small>' : ''}</td>${user.perfil !== 'motorista' ? `<td><button class="quiet" data-edit="${p.id}">Corrigir</button></td>` : ''}</tr>`).join('')}</tbody></table></div>` : '<div class="empty">Nenhum ponto encontrado com esses filtros.</div>');
}

function team() {
    $('#view').innerHTML = `<div class="note">Cada cadastro cria uma conta com perfil próprio. Gerentes acessam apenas os motoristas de sua equipe.</div><section class="panel"><h2>Motoristas</h2>${people.motoristas.length ? `<div class="table-wrap"><table><thead><tr><th>NOME</th><th>TELEFONE</th><th>VEÍCULO</th><th>KM/L</th><th>GERENTE</th></tr></thead><tbody>${people.motoristas.map(m => `<tr><td>${esc(m.nome)}</td><td>${esc(m.telefone)}</td><td>${esc(m.veiculo)}</td><td>${num(m.km_por_litro)}</td><td>${esc(people.gerentes.find(g => g.id === m.gerente_id)?.nome || '—')}</td></tr>`).join('')}</tbody></table></div>` : '<p class="muted">Nenhum motorista cadastrado.</p>'}<details style="margin-top:20px"><summary><b>+ Cadastrar motorista</b></summary><form id="driver-form" style="margin-top:20px"><div class="form-grid">${field('nome', 'Nome')}${field('telefone', 'Telefone', 'tel')}${field('documento', 'Documento')}${field('veiculo', 'Veículo')}${field('km_por_litro', 'Rendimento (km/l)', 'number', 'step="0.01" min="0.01" value="' + params.km_por_litro + '"')}<label>Gerente responsável<select name="gerente_id" required>${people.gerentes.map(g => `<option value="${g.id}">${esc(g.nome)}</option>`).join('')}</select></label>${field('login', 'Usuário de acesso')}${field('senha', 'Senha inicial', 'password', 'minlength="10" autocomplete="new-password"')}</div><div class="form-actions"><button class="primary">Cadastrar motorista</button></div></form></details></section><section class="panel"><h2>Gerentes</h2><div class="table-wrap"><table><thead><tr><th>NOME</th><th>E-MAIL</th><th>TELEFONE</th></tr></thead><tbody>${people.gerentes.map(g => `<tr><td>${esc(g.nome)}</td><td>${esc(g.email)}</td><td>${esc(g.telefone)}</td></tr>`).join('')}</tbody></table></div>${user.perfil === 'administrador' ? `<details style="margin-top:20px"><summary><b>+ Cadastrar gerente</b></summary><form id="manager-form" style="margin-top:20px"><div class="form-grid">${field('nome', 'Nome')}${field('telefone', 'Telefone', 'tel')}${field('email', 'E-mail', 'email')}${field('login', 'Usuário de acesso')}${field('senha', 'Senha inicial', 'password', 'minlength="10" autocomplete="new-password"')}</div><div class="form-actions"><button class="primary">Cadastrar gerente</button></div></form></details>` : ''}</section>`;
}

function field(name, label, type = 'text', attrs = '') {
    return `<label>${label}<input name="${name}" type="${type}" ${attrs} required maxlength="200"></label>`;
}

function settings() {
    $('#view').innerHTML = `<section class="panel"><h2>Parâmetros de custo e jornada</h2><p class="muted">Aplicados aos novos roteiros. O histórico mantém os valores originais.</p><form id="settings-form"><div class="form-grid">${field('valor_combustivel', 'Combustível (R$/litro)', 'number', `step="0.01" min="0" value="${params.valor_combustivel}"`)}${field('km_por_litro', 'Rendimento padrão (km/l)', 'number', `step="0.01" min="0.01" value="${params.km_por_litro}"`)}${field('jornada_padrao_horas', 'Jornada diária (horas)', 'number', `step="0.25" min="0.25" max="24" value="${params.jornada_padrao_horas}"`)}<label>Custo padrão por km (R$)<input id="cost-km" readonly value="${num(params.custo_por_km)}"></label></div><p class="note" style="margin-top:22px">O custo por km é calculado pelo preço do combustível ÷ rendimento. Cada roteiro usa o rendimento cadastrado no veículo do motorista. O padrão acima preenche novos cadastros.</p><h3>Regras do tempo parado</h3><p class="muted">Ponto 1 sempre excluído · Tempo = saída − chegada · Total = soma das paradas encerradas. Estas regras são obrigatórias na especificação e permanecem fixas.</p><div class="form-actions"><button class="primary">Salvar parâmetros</button></div></form></section>`;
}

function audit(rows) {
    $('#view').innerHTML = `<section class="panel"><h2>Registro de alterações</h2><p class="muted">Últimos 500 registros acessíveis ao seu perfil. O histórico completo permanece no banco.</p>${rows.length ? `<div class="table-wrap"><table><thead><tr><th>QUANDO / QUEM</th><th>PONTO</th><th>AÇÃO / MOTIVO</th><th>ALTERAÇÕES</th></tr></thead><tbody>${rows.map(a => { const before = JSON.parse(a.antes), after = JSON.parse(a.depois); const changes = Object.keys(after).filter(k => JSON.stringify(before[k]) !== JSON.stringify(after[k])).map(k => `<div><b>${esc(k)}</b>: ${esc(before[k] ?? '—')} → ${esc(after[k] ?? '—')}</div>`).join(''); return `<tr><td>${stamp(a.instante)}<small>${esc(a.login)}</small></td><td>${a.ponto_id ? '#' + a.ponto_id : 'Parâmetros'}</td><td>${esc(a.acao)}<small>${esc(a.motivo)}</small></td><td><details><summary>Ver alterações</summary>${changes || 'Sem mudança de valores'}</details></td></tr>`; }).join('')}</tbody></table></div>` : '<div class="empty">Nenhuma alteração registrada.</div>'}</section>`;
}

function editPoint(id) {
    const p = report.pontos.find(p => p.id === Number(id));
    const f = $('#edit-form');
    ['id', 'endereco', 'latitude', 'longitude'].forEach(k => f.elements[k].value = p[k]);
    ['data_hora_chegada', 'data_hora_saida'].forEach(k => f.elements[k].value = dateInput(p[k]));
    f.elements.motivo.value = '';
    $('#edit-dialog').showModal();
}

function updateTimers() {
    $$('[data-timer]').forEach(el => el.textContent = duration(Math.max(0, (Date.now() - Date.parse(el.dataset.timer)) / 60000)));
}
$('#login-form').addEventListener('submit', async e => {
    e.preventDefault();
    $('#login-error').textContent = '';
    await action(e.submitter, async () => {
        try {
            await api('/login', 'POST', formData(e.target));
            e.target.reset();
            await boot();
        } catch (err) {
            $('#login-error').textContent = err.message;
        }
    });
});
$('#logout').addEventListener('click', () => action($('#logout'), async () => {
    await api('/logout', 'POST', {});
    showLogin();
}));
$('#refresh').addEventListener('click', () => render());
$('#apply-filter').addEventListener('click', () => render());
$('#close-dialog').addEventListener('click', () => $('#edit-dialog').close());
document.addEventListener('click', async e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.view) {
        view = b.dataset.view;
        await render();
    }
    if (b.dataset.period) setPeriod(b.dataset.period);
    if (b.dataset.go) {
        view = b.dataset.go;
        await render();
    }
    if (b.id === 'add-point') addPoint();
    if (b.hasAttribute('data-remove-point')) {
        if ($('#point-inputs').children.length <= 2) return toast('Mantenha ao menos partida e destino.');
        b.closest('.point-input').remove();
        $$('.point-input').forEach((p, i) => p.querySelector('b').textContent = i + 1);
    }
    if (b.dataset.edit) editPoint(b.dataset.edit);
    if (b.dataset.start) action(b, async () => {
        await api(`/roteiros/${b.dataset.start}/iniciar`, 'POST', {});
        toast('Roteiro iniciado. Registre a partida.');
        await render();
    });
    if (b.dataset.arrive || b.dataset.leave) action(b, async () => {
        await api(`/pontos/${b.dataset.arrive || b.dataset.leave}`, 'POST', {
            acao: b.dataset.arrive ? 'chegada' : 'saida'
        });
        toast('Horário registrado.');
        await render();
    });
    if (b.id === 'export-csv') window.location.href = '/api/exportar.csv?' + query($('#history-search').value);
    if (b.id === 'export-pdf') window.print();
});
document.addEventListener('input', e => {
    if (e.target.id === 'history-search') historyRows();
    if (e.target.closest('#settings-form')) {
        let f = $('#settings-form');
        $('#cost-km').value = num(Number(f.elements.valor_combustivel.value) / Number(f.elements.km_por_litro.value));
    }
});
document.addEventListener('submit', e => {
    let f = e.target;
    if (!['route-form', 'driver-form', 'manager-form', 'settings-form', 'edit-form'].includes(f.id)) return;
    e.preventDefault();
    action(e.submitter, async () => {
        let data = formData(f);
        if (f.id === 'route-form') {
            data.pontos = $$('.point-input').map(p => Object.fromEntries([...p.querySelectorAll('input')].map(i => [i.name, i.value])));
            await api('/roteiros', 'POST', data);
            $('#day').value = data.data;
            setPeriod('dia');
            toast('Roteiro cadastrado.');
        }
        if (f.id === 'driver-form' || f.id === 'manager-form') {
            await api(f.id === 'driver-form' ? '/motoristas' : '/gerentes', 'POST', data);
            people = await api('/pessoas');
            $('#driver-filter').innerHTML = '<option value="">Todos os motoristas</option>' + driverOptions();
            toast('Cadastro criado.');
        }
        if (f.id === 'settings-form') {
            await api('/parametros', 'PUT', data);
            toast('Parâmetros salvos para os próximos roteiros.');
        }
        if (f.id === 'edit-form') {
            ['data_hora_chegada', 'data_hora_saida'].forEach(k => data[k] = data[k] ? new Date(data[k] + '-03:00').toISOString() : null);
            await api('/pontos/' + data.id, 'PUT', data);
            $('#edit-dialog').close();
            toast('Correção salva com auditoria.');
        }
        await render();
    });
});
const today = localDay();
$('#day').value = $('#start').value = $('#end').value = today;
$('#month').value = today.slice(0, 7);
$('#today-label').textContent = new Date().toLocaleDateString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
});
setInterval(updateTimers, 1000);
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => { });
boot();

function enhanceCharts() {
    if (!window.Chart) return;
    const bar = $('.bar-chart');
    if (bar) {
        const parent = document.createElement('div');
        parent.style.height = '250px';
        const canvas = document.createElement('canvas');
        canvas.setAttribute('aria-label', 'Tempo parado e jornada por dia, em minutos');
        canvas.setAttribute('role', 'img');
        parent.append(canvas);
        bar.replaceWith(parent);
        charts.push(new Chart(canvas, {
            type: 'bar',
            data: {
                labels: report.dias.map(d => dateBR(d.data)),
                datasets: [{
                    label: 'Tempo parado (min)',
                    data: report.dias.map(d => d.minutos),
                    backgroundColor: '#167454',
                    borderRadius: 4
                }, {
                    label: 'Jornada (min)',
                    data: report.dias.map(d => d.jornada),
                    backgroundColor: '#dce5e8',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Minutos'
                        },
                        grid: {
                            color: '#edf1f2'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 12
                        }
                    }
                },
            }
        }));
    }
    const donut = $('.donut');
    if (donut) {
        const groups = {};
        report.pontos.filter(p => p.ordem_sequencial > 1).forEach(p => groups[p.endereco] = (groups[p.endereco] || 0) + p.tempo_parado_minutos);
        let entries = Object.entries(groups).filter(e => e[1] > 0).sort((a, b) => b[1] - a[1]);
        if (entries.length > 5) entries = [...entries.slice(0, 5), ['Outros', entries.slice(5).reduce((a, b) => a + b[1], 0)]];
        const parent = document.createElement('div');
        parent.style.cssText = 'width:175px;height:175px;flex-shrink:0';
        const canvas = document.createElement('canvas');
        canvas.setAttribute('aria-label', 'Distribuição de minutos por endereço, descrita na legenda');
        canvas.setAttribute('role', 'img');
        parent.append(canvas);
        donut.replaceWith(parent);
        charts.push(new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    data: entries.map(e => e[1]),
                    backgroundColor: ['#167454', '#84b780', '#bed774', '#597f91', '#a0a8bc', '#d3ab60'],
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }));
    }
}