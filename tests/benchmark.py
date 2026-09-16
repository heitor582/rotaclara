"""Benchmark sintético isolado de consulta de 12 meses (RNF03)."""
import json
import sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from datetime import date,timedelta
from pathlib import Path
import sqlite3
import tempfile
import time
import server

with tempfile.TemporaryDirectory() as tmp:
    db=sqlite3.connect(Path(tmp)/'bench.db');db.row_factory=sqlite3.Row
    db.executescript((server.ROOT/'schema.sql').read_text())
    db.execute("INSERT INTO gerente VALUES (1,'Teste','0','test@example.invalid')")
    for m in range(1,11):
        db.execute('INSERT INTO motorista VALUES (?,?,?,?,?,?,?)',(m,1,f'Motorista {m}','0',f'TEST-{m}','Veiculo',10))
        for d in range(365):
            day=(date(2025,1,1)+timedelta(days=d)).isoformat()
            rid=db.execute('INSERT INTO roteiro(data,motorista_id,distancia_total,tempo_total_parado,custo_estimado,valor_combustivel,km_por_litro,custo_por_km,jornada_padrao_horas) VALUES (?,?,?,?,?,?,?,?,?)',(day,m,100,90,60,6,10,.6,8)).lastrowid
            db.executemany('INSERT INTO ponto(roteiro_id,endereco,latitude,longitude,ordem_sequencial,tempo_parado_minutos) VALUES (?,?,?,?,?,?)',[(rid,f'Endereco {p}',-19,-44,p,0 if p==1 else 10) for p in range(1,11)])
    db.commit();times=[];payload_size=0
    for _ in range(5):
        begin=time.perf_counter()
        report=server.report_data(db,{'perfil':'administrador'},{'inicio':['2025-01-01'],'fim':['2025-12-31']})
        payload=json.dumps(report,ensure_ascii=False).encode();payload_size=len(payload)
        times.append(time.perf_counter()-begin)
    print(json.dumps({'roteiros':3650,'pontos':36500,'consultas':5,'segundos':[round(t,4) for t in times],'pior_tempo_segundos':round(max(times),4),'payload_bytes':payload_size,'meta_consulta_menor_3s':max(times)<3,'limite':'Mede consulta, agregação e serialização local; não inclui rede nem renderização do navegador.'},ensure_ascii=False,indent=2))
    db.close()
