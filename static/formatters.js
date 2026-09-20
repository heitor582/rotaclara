const select = selector => document.querySelector(selector);
const selectAll = selector => [...document.querySelectorAll(selector)];
const escapeHtml = v => String(v ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
}[c]));
const formatCurrency = v => Number(v).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
});
const formatNumber = v => Number(v).toLocaleString('pt-BR', {
    maximumFractionDigits: 1
});
const formatDuration = v => `${Math.floor(v / 60)}h ${Math.floor(v % 60).toString().padStart(2, '0')}min`;
const currentLocalDate = () => new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
}).format(new Date());
const formatDate = v => v ? new Date(v + 'T12:00:00').toLocaleDateString('pt-BR') : '—';
const formatTimestamp = v => v ? new Date(v).toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo'
}) : '—';
const formatTimestampInput = v => v ? new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
}).format(new Date(v)).replace(' ', 'T') : '';

export { select, selectAll, escapeHtml, formatCurrency, formatNumber, formatDuration, currentLocalDate, formatDate, formatTimestamp, formatTimestampInput };
