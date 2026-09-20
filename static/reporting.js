export function summarizeStops(points, maximumAddresses = 5) {
    const totals = new Map();
    for (const point of points) {
        if (point.ordem_sequencial > 1) {
            totals.set(point.endereco, (totals.get(point.endereco) || 0) + point.tempo_parado_minutos);
        }
    }
    const entries = [...totals].filter(([, minutes]) => minutes > 0).sort((first, second) => second[1] - first[1]);
    if (entries.length <= maximumAddresses) return entries;
    const otherMinutes = entries.slice(maximumAddresses).reduce((total, [, minutes]) => total + minutes, 0);
    return [...entries.slice(0, maximumAddresses), ['Outros', otherMinutes]];
}
