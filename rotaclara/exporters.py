import csv
import io

CSV_COLUMNS = ('data', 'roteiro_id', 'motorista', 'ordem_sequencial', 'endereco',
               'data_hora_chegada', 'data_hora_saida', 'tempo_parado_minutos')


def protect_csv_cell(value):
    text = str(value if value is not None else '')
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r')) else text


def export_points_csv(points):
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Data', 'Roteiro', 'Motorista', 'Ordem', 'Endereço', 'Chegada', 'Saída', 'Minutos parados'])
    for point in points:
        writer.writerow([protect_csv_cell(point[column]) for column in CSV_COLUMNS])
    return output.getvalue()
