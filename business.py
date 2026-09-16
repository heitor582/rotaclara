"""Regras de negócio puras. Horários devem conter fuso e são comparados em UTC."""
from datetime import datetime, timezone
import math


def numero(valor, nome, minimo=0, maximo=float('inf')):
    try:
        n = float(valor)
    except (ValueError, TypeError):
        raise ValueError(f'{nome}: informe um número válido.')
    if not math.isfinite(n) or not minimo <= n <= maximo:
        raise ValueError(f'{nome}: valor fora do intervalo permitido.')
    return n


def horario(valor):
    if not valor:
        return None
    try:
        dt = datetime.fromisoformat(valor.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError('Horário inválido.')
    if dt.tzinfo is None:
        raise ValueError('Horário deve incluir fuso horário.')
    return dt.astimezone(timezone.utc)


def calcularTempoParadoPonto(ponto, ordem=None):
    ordem = ponto['ordem_sequencial'] if ordem is None else ordem
    chegada, saida = horario(ponto.get('data_hora_chegada')), horario(ponto.get('data_hora_saida'))
    if saida and not chegada:
        raise ValueError('Registre a chegada antes da saída.')
    if chegada and saida and saida < chegada:
        raise ValueError('A saída não pode ser anterior à chegada.')
    if ordem == 1 or not chegada or not saida:
        return 0.0
    return (saida - chegada).total_seconds() / 60


def calcularTempoTotalRoteiro(listaPontos):
    return sum(calcularTempoParadoPonto(p) for p in listaPontos)


def calcularCustoRoteiro(distanciaKm, valorCombustivel, kmPorLitro):
    distancia = numero(distanciaKm, 'Distância')
    valor = numero(valorCombustivel, 'Combustível')
    rendimento = numero(kmPorLitro, 'Rendimento', 0.000001)
    return distancia * valor / rendimento


def calcularPorcentagemJornada(tempoTotalParadoMinutos, jornadaHoras=8):
    return numero(tempoTotalParadoMinutos, 'Tempo') / (numero(jornadaHoras, 'Jornada', 0.000001) * 60) * 100
