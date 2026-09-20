import test from 'node:test';
import assert from 'node:assert/strict';
import { summarizeStops } from '../static/reporting.js';
import { escapeHtml, formatTimestampInput } from '../static/formatters.js';

test('ranking excludes origin, groups addresses and preserves total in Outros', () => {
    const points = [
        { endereco: 'Base', ordem_sequencial: 1, tempo_parado_minutos: 90 },
        ...['A', 'B', 'A', '__proto__'].map(endereco => ({ endereco, ordem_sequencial: 2, tempo_parado_minutos: 10 }))
    ];
    assert.deepEqual(summarizeStops(points, 1), [['A', 20], ['Outros', 20]]);
    assert.deepEqual(summarizeStops(points).at(-1), ['__proto__', 10]);
});

test('user content is escaped before entering templates', () => {
    assert.equal(escapeHtml('<img onerror="x">&'), '&lt;img onerror=&quot;x&quot;&gt;&amp;');
});

test('point editor converts UTC to operation timezone across midnight', () => {
    assert.equal(formatTimestampInput('2026-09-20T01:30:00Z'), '2026-09-19T22:30:00');
});
