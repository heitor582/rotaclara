import { select, selectAll, escapeHtml, formatNumber, currentLocalDate, formatTimestampInput } from './formatters.js';
import { createApiClient } from './api.js';
import { renderCharts, destroyCharts } from './charts.js';
import { renderDriverOptions, renderDashboard, renderRoutes, appendPointInput, renderHistory, renderHistoryRows, renderTeam, renderSettings, renderAudit, updateStopTimers } from './views.js';
const api = createApiClient(showLogin);
let user, people = {
    motoristas: [],
    gerentes: []
},
    params, report, view = 'dashboard',
    period = 'mes',
    renderId = 0;
let toastTimer;

function showToast(message) {
    select('#toast').textContent = message;
    select('#toast').hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => select('#toast').hidden = true, 6000);
}

const readFormData = form => Object.fromEntries(new FormData(form));
async function runAction(button, action) {
    if (button) button.disabled = true;
    try {
        await action();
    } catch (e) {
        showToast(e.message);
    } finally {
        if (button) button.disabled = false;
    }
}

function showLogin() {
    renderId += 1;
    destroyCharts();
    select('#app').hidden = true;
    select('#login-screen').hidden = false;
    select('#view').replaceChildren();
    select('#edit-dialog').close();
    user = null;
    report = null;
}

function selectedDateRange() {
    if (period === 'dia') return [select('#day').value, select('#day').value];
    if (period === 'mes') {
        const month = select('#month').value;
        const [year, monthNumber] = month.split('-').map(Number);
        return [month + '-01', month + '-' + new Date(year, monthNumber, 0).getDate()];
    }
    return [select('#start').value, select('#end').value];
}

function buildReportQuery(search = '') {
    const [start, end] = selectedDateRange();
    return new URLSearchParams({
        inicio: start,
        fim: end,
        motorista: select('#driver-filter').value,
        status: select('#status-filter').value,
        busca: search
    }).toString();
}

async function initializeSession() {
    try {
        user = await api('/me');
        [people, params] = await Promise.all([api('/pessoas'), api('/parametros')]);
        select('#login-screen').hidden = true;
        select('#app').hidden = false;
        select('#user-name').textContent = user.login;
        select('#user-role').textContent = user.perfil;
        selectAll('[data-manager]').forEach(el => el.hidden = user.perfil === 'motorista');
        select('#driver-filter').innerHTML = '<option value="">Todos os motoristas</option>' + renderDriverOptions(people);
        select('#status-filter').value = '';
        view = 'dashboard';
        setPeriodFilter('mes');
        if (user.perfil === 'motorista') {
            select('#driver-filter').value = user.motorista_id;
            view = 'coleta';
            period = 'dia';
            setPeriodFilter('dia');
        }
        await renderCurrentView();
    } catch (error) {
        showLogin();
        select('#login-error').textContent = error.message;
    }
}

function setPeriodFilter(p) {
    period = p;
    selectAll('[data-period]').forEach(b => b.classList.toggle('active', b.dataset.period === p));
    select('#day-filter').hidden = p !== 'dia';
    select('#month-filter').hidden = p !== 'mes';
    select('#start-filter').hidden = select('#end-filter').hidden = p !== 'periodo';
}
const titles = {
    dashboard: ['Cada minuto, à vista.', 'Tempo parado e custo estimado dos seus roteiros.', 'VISÃO GERAL'],
    coleta: ['O trajeto começa aqui.', 'Organize os pontos e registre cada chegada e saída.', 'ROTEIROS E COLETA'],
    historico: ['O caminho fica registrado.', 'Consulte paradas por endereço e exporte o período.', 'HISTÓRICO'],
    pessoas: ['Quem move a operação.', 'Cadastre profissionais e organize a equipe responsável.', 'EQUIPE'],
    parametros: ['Os números da sua operação.', 'Configure os valores usados nos próximos roteiros.', 'PARÂMETROS'],
    auditoria: ['Cada alteração, rastreável.', 'Consulte quem alterou pontos, horários e parâmetros.', 'AUDITORIA']
};
async function renderCurrentView() {
    const requestId = ++renderId;
    const selectedView = view;
    const search = select('#history-search')?.value || '';
    const [title, subtitle, breadcrumb] = titles[selectedView];
    destroyCharts();
    select('#page-title').textContent = title;
    select('#page-subtitle').textContent = subtitle;
    select('#breadcrumb').textContent = breadcrumb;
    selectAll('[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
    select('#filters').hidden = !['dashboard', 'coleta', 'historico'].includes(view);
    select('#view').innerHTML = '<div class="empty" role="status">Carregando dados…</div>';
    try {
        if (['dashboard', 'coleta', 'historico'].includes(selectedView)) {
            const result = await api('/relatorio?' + buildReportQuery());
            if (requestId !== renderId) return;
            report = result;
        }
        if (selectedView === 'pessoas') {
            const result = await api('/pessoas');
            if (requestId !== renderId) return;
            people = result;
        }
        if (selectedView === 'parametros') {
            const result = await api('/parametros');
            if (requestId !== renderId) return;
            params = result;
        }
        if (selectedView === 'auditoria') {
            const rows = await api('/auditoria');
            if (requestId === renderId) renderAudit(rows);
            return;
        }
        const renderers = { dashboard: renderDashboard, coleta: renderRoutes, historico: renderHistory,
            pessoas: renderTeam, parametros: renderSettings };
        renderers[selectedView]({ user, people, params, report, period, search });
        if (selectedView === 'dashboard') renderCharts(report);
    } catch (error) {
        if (requestId === renderId) select('#view').innerHTML = `<div class="empty error">${escapeHtml(error.message)}</div>`;
    }
}

function openPointEditor(id) {
    const point = report.pontos.find(point => point.id === Number(id));
    const form = select('#edit-form');
    ['id', 'endereco', 'latitude', 'longitude'].forEach(field => form.elements[field].value = point[field]);
    ['data_hora_chegada', 'data_hora_saida'].forEach(field => form.elements[field].value = formatTimestampInput(point[field]));
    form.elements.motivo.value = '';
    select('#edit-dialog').showModal();
}

select('#login-form').addEventListener('submit', async event => {
    event.preventDefault();
    select('#login-error').textContent = '';
    await runAction(event.submitter, async () => {
        try {
            await api('/login', 'POST', readFormData(event.target));
            event.target.reset();
            await initializeSession();
        } catch (error) {
            select('#login-error').textContent = error.message;
        }
    });
});
select('#logout').addEventListener('click', () => runAction(select('#logout'), async () => {
    await api('/logout', 'POST', {});
    showLogin();
}));
select('#refresh').addEventListener('click', () => renderCurrentView());
select('#apply-filter').addEventListener('click', () => renderCurrentView());
select('#close-dialog').addEventListener('click', () => select('#edit-dialog').close());
document.addEventListener('click', async event => {
    const button = event.target.closest('button');
    if (!button) return;
    if (button.hasAttribute('data-pending-filter')) {
        select('#status-filter').value = 'pendencias';
        await renderCurrentView();
        return;
    }
    if (button.dataset.view) {
        view = button.dataset.view;
        await renderCurrentView();
    }
    if (button.dataset.period) setPeriodFilter(button.dataset.period);
    if (button.dataset.go) {
        view = button.dataset.go;
        await renderCurrentView();
    }
    if (button.id === 'add-point') appendPointInput();
    if (button.hasAttribute('data-remove-point')) {
        if (select('#point-inputs').children.length <= 2) return showToast('Mantenha ao menos partida event destino.');
        button.closest('.point-input').remove();
        selectAll('.point-input').forEach((point, i) => point.querySelector('b').textContent = i + 1);
    }
    if (button.dataset.edit) openPointEditor(button.dataset.edit);
    if (button.dataset.start) runAction(button, async () => {
        await api(`/roteiros/${button.dataset.start}/iniciar`, 'POST', {});
        showToast('Roteiro iniciado. Registre a partida.');
        await renderCurrentView();
    });
    if (button.dataset.arrive || button.dataset.leave) runAction(button, async () => {
        await api(`/pontos/${button.dataset.arrive || button.dataset.leave}`, 'POST', {
            acao: button.dataset.arrive ? 'chegada' : 'saida'
        });
        showToast('Horário registrado.');
        await renderCurrentView();
    });
    if (button.id === 'export-csv') window.location.href = '/api/exportar.csv?' + buildReportQuery(select('#history-search').value);
    if (button.id === 'export-pdf') window.print();
});
document.addEventListener('input', event => {
    if (event.target.id === 'history-search') renderHistoryRows({ user, people, params, report, period });
    if (event.target.closest('#settings-form')) {
        let form = select('#settings-form');
        select('#cost-km').value = formatNumber(Number(form.elements.valor_combustivel.value) / Number(form.elements.km_por_litro.value));
    }
});
document.addEventListener('submit', event => {
    let form = event.target;
    if (!['route-form', 'driver-form', 'manager-form', 'settings-form', 'edit-form'].includes(form.id)) return;
    event.preventDefault();
    runAction(event.submitter, async () => {
        let data = readFormData(form);
        if (form.id === 'route-form') {
            data.pontos = selectAll('.point-input').map(point => Object.fromEntries([...point.querySelectorAll('input')].map(i => [i.name, i.value])));
            await api('/roteiros', 'POST', data);
            select('#day').value = data.data;
            setPeriodFilter('dia');
            showToast('Roteiro cadastrado.');
        }
        if (form.id === 'driver-form' || form.id === 'manager-form') {
            await api(form.id === 'driver-form' ? '/motoristas' : '/gerentes', 'POST', data);
            people = await api('/pessoas');
            select('#driver-filter').innerHTML = '<option value="">Todos os motoristas</option>' + renderDriverOptions(people);
            showToast('Cadastro criado.');
        }
        if (form.id === 'settings-form') {
            await api('/parametros', 'PUT', data);
            showToast('Parâmetros salvos para os próximos roteiros.');
        }
        if (form.id === 'edit-form') {
            ['data_hora_chegada', 'data_hora_saida'].forEach(field => data[field] = data[field] ? new Date(data[field] + '-03:00').toISOString() : null);
            await api('/pontos/' + data.id, 'PUT', data);
            select('#edit-dialog').close();
            showToast('Correção salva com auditoria.');
        }
        await renderCurrentView();
    });
});
const today = currentLocalDate();
select('#day').value = select('#start').value = select('#end').value = today;
select('#month').value = today.slice(0, 7);
select('#today-label').textContent = new Date().toLocaleDateString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
});
setInterval(updateStopTimers, 1000);
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => { });
initializeSession();
