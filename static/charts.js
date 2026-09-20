import { select, formatDate } from './formatters.js';
import { summarizeStops } from './reporting.js';
let charts = [];
export function destroyCharts() { charts.forEach(chart => chart.destroy()); charts = []; }
export function renderCharts(report) {
    if (!window.Chart) return;
    const bar = select('.bar-chart');
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
                labels: report.dias.map(d => formatDate(d.data)),
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
    const donut = select('.donut');
    if (donut) {
        const entries = summarizeStops(report.pontos);
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
